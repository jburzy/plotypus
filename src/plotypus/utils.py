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

    if plot_style.get('show_lumi',True):
        lumiStr = str(plot_style.get('lumi_val',139.0)) + " fb^{-1}"
    if plot_style.get('show_com',True):
        comStr = "#sqrt{s} = " + str(plot_style.get('com_val',13))
    
    if plot_style.get('show_lumi',True) and plot_style.get('show_com',True):
        return f"{comStr}, {lumiStr}"
    else:
        return comStr + lumiStr

        


