# plotypus: Another ATLAS plotting package

`plotypus` is a package for plotting `ROOT` histograms. It relies on the [`atlasplots` package](https://github.com/joeycarter/atlas-plots/) for the backend, and `yaml` for the plot specifications. 

## Usage:

Install the package using the `setuptools` script:

```
python setup.py develop
```
This will install the executable `dump-plots`, which takes only a single config file as a parameters:
```
dump-plots config.yaml
```

## Example `yaml` config:

Suppose you wanted to compare the $p_{T}$ distribution of a $Z$ boson candidate between data, background, and a signal sample. An example plot config may contain the following:

### Sample block

The sample config defines all of the samples that will be used in your plots. In general, each sample corresponds to one entry in the legend. The location of the files and the styling are specified here.

Example:

```
samples:
  - sample: &signal
      name: "signal"
      files: ["signal.root"]
      legend: "Signal"
      style:
        linecolor: '#01BAEF'
        linestyle: 2
        linewidth: 2
        markerstyle: 20
        markersize: 0.0
      legend_format: "L"
      scale: 100.0
  - sample: &data
      name: "data"
      files: ["data15.root","data16.root","data17.root","data18.root"]
      style:
        linecolor: '#00000'
        linewidth: 2
        markerstyle: 20
        markersize: 1.0
      draw_style: "P"
      legend: "Data"
      legend_format: "pe"
      is_data: True
      numerator: True
  - sample: &VJets
      name: "V+Jets"
      files: ["Zjets.root, Wjets.root"]
      style:
        linecolor: '#7CFFC4'
        fillcolor: '#7CFFC4'
        linewidth: 2
        markerstyle: 20
        markersize: 1.0
      legend: "V+jets"
      legend_format: "f"
      stack: True
      is_data: False
  - sample: &ttbar
      name: "ttbar"
      files: ["ttbar.root"]
      style:
        linecolor: '#FC7753'
        fillcolor: '#FC7753'
        linewidth: 2
      legend: "ttbar"
      legend_format: "f"
      stack: True
      is_data: False
```

### Style block

The style block defines the base style for your plots. This is optional, but helps you stay [DRY](https://www.digitalocean.com/community/tutorials/what-is-dry-development) if you want to ex. plot the same variable for multiple selections. 

Example:

```
plot_styles:
  - plot: &base
      y_min: 0
      lumi_val: 139.0
      com_val: 13
      show_lumi: True
      show_com: True
      show_atlas: True
      atlas_mod: "Internal"
      y_axis_props:
        max_digits: 3
  - plot: &pt
      <<: *base
      ratio: True
      log_scale_y: True
      x_min: 0
      x_max: 250
      y_min: 0.1
      units: "GeV"
```

### Plot block

Finally, the plot block specifies the actual plots that will be written out. Each block corresponds to one final pdf that will be created.

Example:

```
plots:
  - name: "l1l2_pt"
    samples:
      - *ttbar
      - *VJets
      - *signal
      - *data
    path: "HtoDVHistsAlgo_SRZ/l1l2_pt"
    style: 
      <<: *pt
      x_label: "p_{T,ll}"
```
