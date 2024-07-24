import atlasplots as aplt
import ROOT
import glob
from .utils import getObj, getLumiStr

def get_x_label(plot: dict) -> str:

    label = plot.get('x_label','')
    if plot.get('units'):
        label += f" [{plot.get('units')}]"
    return label

def get_y_label(plot: dict, bin_width: str = '', draw_units: bool = False) -> str:

    label = plot.get('y_label',"Events")
    if plot.get('units') and draw_units:
        label += f" / {bin_width} {plot.get('units')}"
    if plot.get('normalize') and plot.get('norm_strategy') == 'area':
        label = "Fraction of " + label
    return label


def make_plot(plot: dict) -> None:
    # Set the ATLAS Style
    aplt.set_atlas_style()
    ROOT.TGaxis.SetMaxDigits(4)

    plot_style = plot['style']
    ratio = plot_style.get('ratio')

    numerators = []
    denominators = []

    # Create a figure and axes
    if ratio:
        fig, (ax1, ax2) = aplt.ratio_plot(name=plot['name'], figsize=(800, 800), hspace=0.10)
        ax1.set_pad_margins(top=0.065, left=0.14)
        ax2.set_pad_margins(left=0.14)
    else:
        fig, ax1 = aplt.subplots(1, 1, name=plot['name'], figsize=(800, 600))
        ax1.set_pad_margins(top=0.065, left=0.13)


    # create legend
    legend = ax1.legend(
        loc=(plot_style.get('legend_x',0.5), 
             1 - ROOT.gPad.GetTopMargin() - 0.05 - 0.08*len(plot['samples'])*plot_style.get('legend_scale',1.0)*plot_style.get('squeeze_legend',1.0), 
             1 - ROOT.gPad.GetRightMargin() - 0.1, 
             1 - ROOT.gPad.GetTopMargin() - 0.05),
        textsize=22*plot_style.get('legend_scale',1.0)
    )
    if plot_style.get('ratio_legend'):
        ratio_legend = ax2.legend(
            loc=(plot_style.get('ratio_legend_x',0.5), 
                 plot_style.get('ratio_legend_y',0.5) - 0.1,
                 plot_style.get('ratio_legend_x',0.5) + 0.2,
                 plot_style.get('ratio_legend_y',0.5)),
            textsize=22*plot_style.get('ratio_legend_scale',1.0)
        )

    # need to keep the tfiles open
    tfiles = []
    hists = {}

    draw_stack = False
    stack =  ROOT.THStack("hist_stack","")
    err_band = None

    for sample in plot['samples']:
        obj = None

        if draw_stack and not sample.get('stack'):
            ax1.plot(stack)
            draw_stack = False
            if not denominators:
                denominators.append(stack)

        for fpath in sample['files']:
            files = glob.glob(fpath)
            for f in files:
                tf = ROOT.TFile(f)
                tfiles.append(tf)
                path = ""
                if isinstance(plot.get('paths'), dict):
                    path = plot.get('paths')[sample['name']]
                else:
                    path = plot.get('paths')
                tmp_obj = getObj(tf, path, sample['type'])
                if obj:
                    obj += tmp_obj
                else:
                    obj = tmp_obj

        if isinstance(obj,ROOT.TEfficiency):
            obj = obj.CreateGraph()

        if plot_style.get('rebin') and isinstance(obj,ROOT.TH1):
            rebin = plot_style['rebin']
            if isinstance(rebin, list):
                import array
                xbins = array.array('d', rebin)
                obj = obj.Rebin(len(xbins)-1, obj.GetName() + sample['name'] + "_rebin", xbins)
            else:
                obj = obj.Rebin(rebin, obj.GetName() + "_rebin")

        if plot_style.get('normalize'):
            if plot_style.get('norm_strategy') == "area":
                if obj.Integral() > 0:
                    obj.Scale(1.0/obj.Integral())
            elif plot_style.get('norm_strategy') == "width":
                obj.Scale(1.0, "width")
                obj.Scale(4.0)

        legend_text = sample.get('legend','')
        if sample.get('scale', 1.0) != 1.0:
            obj.Scale(sample.get('scale'))
            if sample.get('add_scale_to_legend',False):
                legend_text += f" (#times{sample.get('scale')})"

        if sample.get('is_data'):
            obj.SetBinErrorOption(ROOT.TH1.EBinErrorOpt.kPoisson)
            obj_graph = aplt.root_helpers.hist_to_graph(obj)
            ax1.plot(obj_graph, options=sample['draw_style'], **sample['style'])
            legend.AddEntry(obj_graph, legend_text, sample['legend_format'])
            hists[sample['name']+'graph'] = obj_graph
        elif sample.get('stack'):
            aplt.root_helpers.set_graphics_attributes(obj, **sample['style'])
            stack.Add(obj)
            draw_stack = True
            legend.AddEntry(obj, legend_text, sample['legend_format'])
        else:
            ax1.plot(obj, options=sample['draw_style'], **sample['style'])
            if isinstance(obj, ROOT.TH1) and sample.get('draw_band',True):
                err_band = aplt.root_helpers.hist_to_graph(
                    obj,
                    show_bin_width=True
                )
                hists[sample['name']+'err'] = err_band
                ax1.plot(err_band, options="2 same",
                         linecolor=obj.GetLineColor(), fillcolor=obj.GetLineColor(),
                         fillalpha=0.35, fillstyle=1001, linewidth=2, linestyle=obj.GetLineStyle(),
                         )
                ax1.plot(obj, options=sample['draw_style'], **sample['style'])
                legend.AddEntry(err_band, legend_text, sample['legend_format'])
            else:
                legend.AddEntry(obj, legend_text, sample['legend_format'])

        if sample['name'] in plot_style.get('numerators',[]):
            numerators.append(obj)
        if sample['name'] in plot_style.get('denominators',[]):
            denominators.append(obj)
        hists[sample['name']] = obj

    if stack.GetHists():
        # Plot the MC stat error as a hatched band
        err_band = aplt.root_helpers.hist_to_graph(
            stack.GetStack().Last(),
            show_bin_width=True
        )
        ax1.plot(err_band, options="2 same", fillcolor=1, fillstyle=3254, linewidth=0)
        err_label = plot_style.get('err_label',"MC Stat. Unc.")
        legend.AddEntry(err_band, err_label, "F")

    if plot_style.get('log_scale_y'):
        ax1.set_yscale("log") 
    if plot_style.get('log_scale_x'):
        ax1.set_xscale("log") 

    # Set axis titles
    (ax2 if ratio else ax1).set_xlabel(get_x_label(plot_style), titleoffset=1.3, **plot_style)
    if ratio:
        ax1.frame.GetXaxis().SetLabelSize(0)
    if isinstance(obj, ROOT.TH1):
        ax1.set_ylabel(get_y_label(plot_style, str(obj.GetBinWidth(1)) if not
            plot_style.get('norm_strategy') == 'width' else '4.0', isinstance(obj, ROOT.TH1)), maxdigits=3, titleoffset=plot_style.get('title_offset',1.75), titlesize=plot_style.get('title_size',28))
    else:
        ax1.set_ylabel(get_y_label(plot_style, '' if not
            plot_style.get('norm_strategy') == 'width' else '', isinstance(obj, ROOT.TH1)), maxdigits=3, titleoffset=plot_style.get('title_offset',1.75), titlesize=plot_style.get('title_size',28))
#        ax1.set_ylabel(get_y_label(plot_style, ''))

    # set the main axis limits
    ax1.set_xlim(plot_style.get('x_min'), plot_style.get('x_max'))
    ax1.set_ylim(plot_style.get('y_min'), plot_style.get('y_max'))

    if plot_style.get('plot_material',False):
         coords = [33.5,50.5,88.5,122.5,299.0]
         tex    = ["IBL","PIX1","PIX2","PIX3","SCT1"]
         for coord,t in zip(coords,tex):
             if coord > (ax1.get_xlim()[1] - 10):
                 break
             line = ROOT.TLine()
             line.SetLineColor(ROOT.kGray)
             line.SetLineWidth(2)
             line.SetLineStyle(1)
             line.DrawLine(coord,0,coord,(1.0*ax1.get_ylim()[1] if plot_style.get('log_scale_y') else 0.95*ax1.get_ylim()[1]))
             ax1.text(0.15+coord/(435 - 300*(350/ax1.get_xlim()[1] - 1)), 0.55 if plot_style.get('log_scale_y') else
             0.53, t,
                      size = 0.045 * .6,
                      font = 42,
                      angle = 45)
             if(coords.index(coord) == 0):
                 legend.AddEntry(line, "Active layers", "l")

    if plot_style.get('plot_extra_line',False):
         line = ROOT.TLine()
         line.SetLineColor(1)
         line.SetLineWidth(1)
         line.SetLineStyle(2)
         line.DrawLine(0,1.0,350,1.0)

    if ratio and (not numerators or not denominators):
        raise RuntimeError("Ratio requested but no numerator or denominator specified. Aborting")


    
    ratios = []
    if ratio:
        # Draw line at y=1 in ratio panel
        line = ROOT.TLine(ax1.get_xlim()[0], plot_style.get('ratio_line',1), ax1.get_xlim()[1], plot_style.get('ratio_line',1))
        line.SetLineStyle(2)
        ax2.plot(line)

        index = 0
        for numerator,denominator in zip(numerators,denominators):
            if plot_style.get('plot_relative_error',True):
                if stack.GetHists():
                    # Plot the relative error on the ratio axes
                    err_band_ratio = aplt.root_helpers.hist_to_graph(
                        stack.GetStack().Last(),
                        show_bin_width=True,
                        norm=True
                    )
                    ax2.plot(err_band_ratio, options="2 same", fillcolor=1, fillstyle=3254)
                else:
                    # Plot the relative error on the ratio axes
                    err_band_ratio = aplt.root_helpers.hist_to_graph(
                        denominator,
                        show_bin_width=True,
                        norm=True
                    )
                    ax2.plot(err_band_ratio, options="2 same", fillcolor=1, fillstyle=3254, linewidth=0)
                    # ratio_legend.AddEntry(err_band_ratio, "Sim. Stat. Unc.", "LF")
            # calculate and draw the ratio
            ratio_hist = numerator.Clone("ratio_hist")
            ratio_hist.Sumw2()
            if isinstance(denominator, ROOT.THStack):
                ratio_hist.Divide(denominator.GetStack().Last())
            elif isinstance(denominator, ROOT.TProfile):
                ratio_hist = ratio_hist.ProjectionX("")
                ratio_hist.Sumw2()
                denominator_hist = denominator.ProjectionX("")
                if plot_style.get('plot_relative_error',True):
                    for i in range(denominator_hist.GetNbinsX()):
                        denominator_hist.SetBinError(i,0)
                ratio_hist.Divide(denominator_hist)
            else:
                denominator_hist = denominator.Clone("")
                if plot_style.get('plot_relative_error',True):
                    for i in range(denominator_hist.GetNbinsX()):
                        denominator_hist.SetBinError(i,0)
                ratio_hist.Divide(denominator_hist)
            ratio_graph = None
            if numerator.GetMarkerSize() != 0:
                ratio_graph = aplt.root_helpers.hist_to_graph(ratio_hist)
                ax2.plot(ratio_graph, options="P0", linewidth=2, linestyle=numerator.GetLineStyle())
                #if plot_style.get('ratio_legend'):
                #    ratio_legend.AddEntry(ratio_graph, plot_style.get('ratio_legend_text')[index], "pe")
            else:
                ratio_graph = aplt.root_helpers.hist_to_graph(ratio_hist, show_bin_width=True)
                ax2.plot(ratio_hist, options="hist", linewidth=2, linecolor=ROOT.kBlack, linestyle=numerator.GetLineStyle())
                ax2.plot(ratio_graph, options="E2", linewidth=2, fillalpha=0.35, fillstyle=1001, fillcolor=ROOT.kBlack, linestyle=numerator.GetLineStyle())
                #if plot_style.get('ratio_legend'):
                #    ratio_legend.AddEntry(ratio_graph, plot_style.get('ratio_legend_text')[index], "lf")
            ratios.append(ratio_graph)
            ratios.append(ratio_hist)

            ax2.set_xlim(ax1.get_xlim())
            ax2.set_ylim(plot_style.get('ratio_min',0.75), plot_style.get('ratio_max',1.25))
            if plot_style.get('ratio_log_scale_y',False):
                ax2.set_yscale("log") 
            ax2.set_ylabel(plot_style.get('ratio_label','Data/MC'), loc="centre", titleoffset=plot_style.get('title_offset',1.75), titlesize=plot_style.get('title_size',28))

            if plot_style.get('draw_arrows',True):
                ax2.draw_arrows_outside_range(ratio_graph)
            index += 1 

    # Go back to top axes to add labels
    ax1.cd()
    legend.Draw()
    if plot_style.get('ratio_legend'):
        ax2.cd()
        #ratio_legend.Draw()
    ax1.cd()
    # Add extra space at top of plot to make room for labels
    ax1.add_margins(top=plot_style.get('pad_top',0.20))

    # Add the ATLAS Label
    if plot_style.get('show_atlas',True):
        aplt.atlas_label(text=plot_style.get('atlas_mod','Internal'), loc="upper left")

    lumi_text = getLumiStr(plot_style)
    ax1.text(plot.get('lumi_x',0.18), 
             plot.get('lumi_y',0.84),
             lumi_text, 
             size=plot.get('lumi_size',22), 
             align=13)

    if plot_style.get('extra_text',[]):
        y_pos = plot_style.get('extra_y',0.79)

        for txt in plot_style['extra_text']:
            ax1.text(plot_style.get('extra_x',0.18), 
                     y_pos,
                     txt, 
                     size=plot_style.get('extra_size',22), 
                     align=13)
            y_pos -= 0.05

    if plot_style.get('label',''):
        ax1.text(plot.get('label_x',1-ROOT.gPad.GetRightMargin()-(0.0135*len(plot_style.get('label')))), 
                 plot.get('label_y',0.97),
                 plot_style.get('label'),
                 size=plot.get('label_size',18), 
                 align=13)


    ax1.pad.RedrawAxis()
    fig.savefig(f"{plot['name']}.pdf")
