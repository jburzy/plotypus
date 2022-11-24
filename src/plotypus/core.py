import atlasplots as aplt
import ROOT

def get_x_label(plot: dict) -> str:

    label = plot['x_label']

    if plot.get('units'):
        label += f" {plot.get['units']}"

    return label

def get_y_label(plot: dict, bin_width: float = None) -> str:

    label = plot.get('y_label',"Events")

    if plot.get('units'):
        label += f" / {bin_width} {plot.get['units']}"

    return label

def make_plot(plot: dict) -> None:
    # Set the ATLAS Style
    aplt.set_atlas_style()

    ratio = plot.get('ratio')

    numerator = None
    denominator = None

    # Create a figure and axes
    if ratio:
        fig, (ax1, ax2) = aplt.ratio_plot(name="fig1", figsize=(800, 800), hspace=0.10)
    else:
        fig, ax1 = aplt.subplots(1, 1, name="fig1", figsize=(800, 600))

    # create legend
    legend = ax1.legend(
        loc=(0.68, 0.75, 1 - ROOT.gPad.GetRightMargin() - 0.03, 1 - ROOT.gPad.GetTopMargin() - 0.03),
        textsize=22
    )

    # need to keep the tfiles open
    tfiles = []

    for sample in plot['samples']:
        tfile = ROOT.TFile(sample['files'][0])
        tfiles.append(tfile)
        obj = tfile.Get(plot['path'])

        if plot.get('rebin'):
            rebin = plot['rebin']
            if isinstance(rebin, list):
                import array
                xbins = array.array('d', rebin)
                obj = obj.Rebin(len(xbins)-1, obj.GetName() + "_rebin", xbins)
            else:
                obj = obj.Rebin(rebin, obj.GetName() + "_rebin")

        if sample.get('is_data'):
            obj.SetBinErrorOption(ROOT.TH1.EBinErrorOpt.kPoisson)
            obj_graph = aplt.root_helpers.hist_to_graph(obj)
            ax1.plot(obj_graph, 'P')
            legend.AddEntry(obj_graph, sample['name'], sample['legend_format'])
        else:
            ax1.plot(obj, sample['draw_style'], label=sample['legend'], labelfmt=sample['legend_format'], **sample['style'])
            legend.AddEntry(obj, sample['name'], sample['legend_format'])

        if sample.get('numerator'):
            numerator = obj
        if sample.get('denominator'):
            denominator = obj

    if ratio and (not numerator or not denominator):
        raise RuntimeError("Ratio requested but no numerator or denominator specified. Aborting")

    if plot.get('log_scale_y'):
        ax1.set_yscale("log") 

    # Set axis titles
    (ax2 if ratio else ax1).set_xlabel(get_x_label(plot))
    ax1.set_ylabel(get_y_label(plot, obj.GetBinWidth(1)))

    # set the main axis limits
    ax1.set_xlim(plot.get('x_min'), plot.get('x_max'))
    ax1.set_ylim(plot.get('y_min'), plot.get('y_max'))
    
    if ratio:
        # Calculate and draw the ratio
        ratio_hist = numerator.Clone("ratio_hist")
        ratio_hist.Divide(denominator)
        ratio_graph = aplt.root_helpers.hist_to_graph(ratio_hist)
        ax2.plot(ratio_graph, "P0")

        # Draw line at y=1 in ratio panel
        line = ROOT.TLine(ax1.get_xlim()[0], plot.get('ratio_line',1), ax1.get_xlim()[1], plot.get('ratio_line',1))
        ax2.plot(line)

        ax2.set_xlim(ax1.get_xlim())
        ax2.set_ylim(plot.get('ratio_min',0.75), plot.get('ratio_min',1.25))
        ax2.set_ylabel(plot.get('ratio_label','Data/MC'), loc="centre")

        if plot.get('draw_arrows'):
            ax2.draw_arrows_outside_range(ratio_graph)

    # Go back to top axes to add labels
    ax1.cd()
    # Add extra space at top of plot to make room for labels
    ax1.add_margins(top=plot.get('pad_top'))

    # Add the ATLAS Label
    aplt.atlas_label(text="Internal", loc="upper left")
    ax1.text(0.2, 0.84, "#sqrt{s} = 13 TeV, 139 fb^{-1}", size=22, align=13)

    fig.savefig("test.pdf")
