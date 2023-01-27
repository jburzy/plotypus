import atlasplots as aplt
import ROOT
from .utils import getObj, getLumiStr

def get_x_label(plot: dict) -> str:

    label = plot['x_label']
    if plot.get('units'):
        label += f" [{plot.get('units')}]"
    return label

def get_y_label(plot: dict, bin_width: str = '', draw_units: bool = False, is2D: bool = False) -> str:

    label = plot.get('y_label',"Events")
    if plot.get('y_units'):
        label += f" [{plot.get('y_units')}]"
    elif plot.get('units') and draw_units:
        label += f" / {bin_width} {plot.get('units')}"
    if plot.get('normalize') and plot.get('norm_strategy') == 'area' and not is2D:
        label = "Fraction of " + label
    return label

def make_plot(plot: dict) -> None:
    # Set the ATLAS Style
    aplt.set_atlas_style()

    plot_style = plot['style']
    ratio = plot_style.get('ratio')
    is2D = plot_style.get('2D')
    
    if ratio and is2D:
        RuntimeError("Ratio plot requested for 2D histogram. Aborting.")
    
    numerator = None
    denominator = None

    # Create a figure and axes
    if ratio:
        fig, (ax1, ax2) = aplt.ratio_plot(name=plot['name'], figsize=(800, 800), hspace=0.10)
        ax1.set_pad_margins(top=0.065, left=0.14)
        ax2.set_pad_margins(left=0.14)
    elif is2D:
        fig, ax1 = aplt.subplots(1, 1, name=plot['name'], figsize=(800, 600))
        ax1.set_pad_margins(top=0.08, right=0.2, left=0.13) 
    else:       
        fig, ax1 = aplt.subplots(1, 1, name=plot['name'], figsize=(800, 600))
        ax1.set_pad_margins(top=0.065, left=0.13)


    # create legend
    legend = ax1.legend(
        loc=(0.5, 0.65, 1 - ROOT.gPad.GetRightMargin() - 0.05, 1 - ROOT.gPad.GetTopMargin() - 0.05),
        textsize=22
    )

    # need to keep the tfiles open
    tfiles = []
    hists = {}

    if is2D and len(plot['samples']) != 1:
        raise RuntimeError("2D histogram must only use one sample. Check config for {}.".format(plot['name']))
    
    draw_stack = False
    stack =  ROOT.THStack("hist_stack","")
    err_band = None

    for sample in plot['samples']:
        obj = None

        if draw_stack and not sample.get('stack') and not is2D:
            ax1.plot(stack)
            draw_stack = False
            if not denominator:
                denominator = stack

        for f in sample['files']:
            tf = ROOT.TFile(f)
            tfiles.append(tf)
            path = ""
            if isinstance(plot.get('paths'), dict):
                path = plot.get('paths')[sample['name']]
            else:
                path = plot.get('paths')
            tmp_obj = getObj(tf, path, sample['type'])
            if obj:
                obj.Add(tmp_obj) 
            else:
                obj = tmp_obj

        if plot_style.get('rebin'):
            rebin = plot_style['rebin']
            if is2D:
                rebin_y = 1
                if plot_style.get('rebin_y'):
                    rebin_y = plot_style['rebin_y']
                obj = obj.Rebin2D(rebin, rebin_y, obj.GetName() + "_rebin2D")
            else:
                if isinstance(rebin, list):
                    import array
                    xbins = array.array('d', rebin)
                    obj = obj.Rebin(len(xbins)-1, obj.GetName() + sample['name'] + "_rebin", xbins)
                else:
                    obj = obj.Rebin(rebin, obj.GetName() + "_rebin")
            
        if plot_style.get('normalize'):
            if is2D and plot_style.get('norm_strategy') != "area":
                raise RuntimeError("2D histograms can only be normalised by area. Check config for {}.".format(plot['name']))
            else:
                if plot_style.get('norm_strategy') == "area":
                    obj.Scale(1.0/obj.Integral())
                elif plot_style.get('norm_strategy') == "width":
                    obj.Scale(1.0, "width")

        legend_text = sample.get('legend','')
        if sample.get('scale', 1.0) != 1.0:
            obj.Scale(sample.get('scale'))
            legend_text += f" (#times{sample.get('scale')})"

        if sample.get('is_data') and not is2D:
            obj.SetBinErrorOption(ROOT.TH1.EBinErrorOpt.kPoisson)
            obj_graph = aplt.root_helpers.hist_to_graph(obj)
            ax1.plot(obj_graph, options=sample['draw_style'], **sample['style'])
            legend.AddEntry(obj_graph, legend_text, sample['legend_format'])
            hists[sample['name']+'graph'] = obj_graph
        elif sample.get('stack') and not is2D: 
            aplt.root_helpers.set_graphics_attributes(obj, **sample['style'])
            stack.Add(obj)
            draw_stack = True
            legend.AddEntry(obj, legend_text, sample['legend_format'])
        else:
            if is2D:
                ax1.plot2d(obj, "COLZ")
            else:
                ax1.plot(obj, options=sample['draw_style'], **sample['style'])
                if isinstance(obj, ROOT.TH1):
                    err_band = aplt.root_helpers.hist_to_graph(
                        obj,
                        show_bin_width=True
                    )
                    hists[sample['name']+'err'] = err_band
                    ax1.plot(err_band, options="2 same", fillcolor=obj.GetLineColor(), fillalpha=0.35, fillstyle=1001, linewidth=0)
                legend.AddEntry(obj, legend_text, sample['legend_format'])

        if sample.get('numerator'):
            numerator = obj
        if sample.get('denominator'):
            denominator = obj
        hists[sample['name']] = obj

    if stack.GetHists():
        # Plot the MC stat error as a hatched band
        err_band = aplt.root_helpers.hist_to_graph(
            stack.GetStack().Last(),
            show_bin_width=True
        )
        ax1.plot(err_band, options="2 same", fillcolor=1, fillstyle=3254, linewidth=0)
        legend.AddEntry(err_band, "MC Stat. Unc.", "F")

    if ratio and (not numerator or not denominator):
        raise RuntimeError("Ratio requested but no numerator or denominator specified. Aborting")

    if plot_style.get('log_scale_y'):
        ax1.set_yscale("log") 
    if plot_style.get('log_scale_x'):
        ax1.set_xscale("log") 

    # Set axis titles
    (ax2 if ratio else ax1).set_xlabel(get_x_label(plot_style), titleoffset=1.3)
    if not isinstance(obj, ROOT.TH2):
        ax1.set_ylabel(get_y_label(plot_style, str(obj.GetBinWidth(1)) if not
            plot_style.get('norm_strategy') == 'width' else '', isinstance(obj, ROOT.TH1)), maxdigits=3, titleoffset=1.7)
    else:
        ax1.set_ylabel(get_y_label(plot_style, '', is2D=is2D))

    # set the main axis limits
    ax1.set_xlim(plot_style.get('x_min'), plot_style.get('x_max'))
    ax1.set_ylim(plot_style.get('y_min'), plot_style.get('y_max'))
    
    if ratio:
        # Draw line at y=1 in ratio panel
        line = ROOT.TLine(ax1.get_xlim()[0], plot_style.get('ratio_line',1), ax1.get_xlim()[1], plot_style.get('ratio_line',1))
        line.SetLineStyle(2)
        ax2.plot(line)

        if stack.GetHists():
            # Plot the relative error on the ratio axes
            err_band_ratio = aplt.root_helpers.hist_to_graph(
                stack.GetStack().Last(),
                show_bin_width=True,
                norm=True
            )
            ax2.plot(err_band_ratio, options="2 same", fillcolor=1, fillstyle=3254)

        # calculate and draw the ratio
        ratio_hist = numerator.Clone("ratio_hist")
        if isinstance(denominator, ROOT.THStack):
            ratio_hist.Divide(denominator.GetStack().Last())
        else:
            ratio_hist.Divide(denominator)
        ratio_graph = aplt.root_helpers.hist_to_graph(ratio_hist)
        ax2.plot(ratio_graph, options="P0", linewidth=2)

        ax2.set_xlim(ax1.get_xlim())
        ax2.set_ylim(plot_style.get('ratio_min',0.75), plot_style.get('ratio_max',1.25))
        ax2.set_ylabel(plot_style.get('ratio_label','Data/MC'), loc="centre")

        if plot_style.get('draw_arrows',True):
            ax2.draw_arrows_outside_range(ratio_graph)
        

    # Go back to top axes to add labels
    ax1.cd()
    # Add extra space at top of plot to make room for labels
    ax1.add_margins(top=plot_style.get('pad_top',0.20))

    # Add the ATLAS Label
    if plot_style.get('show_atlas',True):
        if is2D:
            aplt.atlas_label(ax1.pad.GetLeftMargin(), 0.97, text=plot_style.get('atlas_mod','Internal'), align=13)
        else:
            aplt.atlas_label(text=plot_style.get('atlas_mod','Internal'), loc="upper left")

    lumi_text = getLumiStr(plot_style)
    if is2D:
        ax1.text(1-ax1.pad.GetRightMargin(), 
                 0.97, 
                 lumi_text, 
                 size=22, 
                 align=33)
    else:
        ax1.text(plot.get('lumi_x',0.18), 
                 plot.get('lumi_y',0.84),
                 lumi_text, 
                 size=plot.get('lumi_size',22), 
                 align=13)

    if plot_style.get('label',''):
        if is2D:
            raise RuntimeError("Additional labels currently not supported for 2D histograms. Aborting.")
        ax1.text(plot.get('label_x',1-ROOT.gPad.GetRightMargin()-(0.0135*len(plot_style.get('label')))), 
                 plot.get('label_y',0.97),
                 plot_style.get('label'),
                 size=plot.get('label_size',18), 
                 align=13)

    ax1.pad.RedrawAxis()
    fig.savefig(f"{plot['name']}.pdf")
