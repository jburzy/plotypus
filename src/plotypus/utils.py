import ROOT

def getObj(tf: ROOT.TFile, path: str, file_type: str) -> ROOT.TObject:

    # TODO: implement drawing from TTrees
    # - need to think about weighting
    obj = None
    if(file_type == 'hist'):
        obj = tf.Get(path).Clone()
    elif(file_type == 'tree'):
        pass

    return obj

def getLumiStr(plot_style: dict) -> str:

    lumiStr = ""
    comStr = ""

    if plot_style['show_lumi']:
        lumiStr = str(plot_style['lumi_val']) + " fb^{-1}"
    if plot_style['show_com']:
        comStr = "#sqrt{s} = " + str(plot_style['com_val'])
    
    if plot_style['show_lumi'] and plot_style['show_com']:
        return f"{comStr}, {lumiStr}"
    else:
        return comStr + lumiStr

        


