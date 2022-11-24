import atlasplots as aplt
import ROOT

def make_plot(plot: dict) -> None:

    # Set the ATLAS Style
    aplt.set_atlas_style()

    ratio = plot.get('ratio')

    # Create a figure and axes
    if ratio:
        fig, (ax1, ax2) = aplt.ratio_plot(name="fig1", figsize=(800, 800), hspace=0.05)
    else:
        fig, ax1 = aplt.subplots(1, 1, name="fig1", figsize=(800, 600))


    # create legend
    legend = ax1.legend(
        loc=(0.68, 0.65, 1 - ROOT.gPad.GetRightMargin() - 0.03, 1 - ROOT.gPad.GetTopMargin() - 0.03),
        textsize=22
    )

    for sample in plot['samples']:
        tfile = ROOT.TFile(sample['files'][0])
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


    if plot.get('log_scale_y'):
        ax1.set_yscale("log") 


    # Go back to top axes to add labels
    ax1.cd()

    # set the main axis limits
    ax1.set_xlim(plot.get('x_min'), plot.get('x_max'))
    ax1.set_ylim(plot.get('y_min'), plot.get('y_max'))
    # Use same x-range in lower axes as upper axes
    if ratio:
        ax2.set_xlim(ax1.get_xlim())

    # Add extra space at top of plot to make room for labels
    ax1.add_margins(top=plot.get('pad_top'))

    # Add the ATLAS Label
    aplt.atlas_label(text="Internal", loc="upper left")
    ax1.text(0.2, 0.84, "#sqrt{s} = 13 TeV, 139 fb^{-1}", size=22, align=13)

    fig.savefig("test.pdf")
