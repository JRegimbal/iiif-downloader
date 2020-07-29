# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from threading import Thread
import utils
import wx


class MainWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="IIIF Downloader")
        dirlabel = wx.StaticText(self, label="Directory to Save Images: ")
        self.dirpicker = wx.DirPickerCtrl(self)

        self.dirsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dirsizer.Add(dirlabel)
        self.dirsizer.Add(self.dirpicker)

        urllabel = wx.StaticText(self, label="URL to IIIF Manifest: ")
        self.urlsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.urlsizer.Add(urllabel)
        self.urlinput = wx.TextCtrl(self)
        self.urlsizer.Add(self.urlinput, flag=wx.EXPAND)

        self.startbutton = wx.Button(self, label="Start")
        self.Bind(wx.EVT_BUTTON, self.onStart, self.startbutton)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.dirsizer, flag=wx.ALIGN_CENTER)
        self.sizer.Add(self.urlsizer, flag=wx.ALIGN_CENTER)
        self.sizer.Add(self.startbutton, flag=wx.ALIGN_CENTER)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show()

    def onStart(self, e):
        path = self.dirpicker.GetPath()
        raw_url = self.urlinput.GetValue()
        isvalid = True
        msg = ""
        manifest = utils.get_manifest(raw_url)
        if path == "":
            isvalid = False
            msg = "A directory must be selected!"
        elif not os.path.exists(path):
            isvalid = False
            msg = "\"{}\" does not exist!".format(path)
        elif not os.path.isdir(path):
            isvalid = False
            msg = "\"{}\" is not a directory!".format(path)
        elif manifest is None:
            isvalid = False
            msg = "Could not download IIIF Presentation Manifest at URL!"
        elif len(manifest.sequences) == 0:
            isvalid = False
            msg = "No sequences in this manifest!"

        if not isvalid:
            msgdlg = wx.MessageDialog(
                self,
                msg,
                caption="IIIF Downloader - Error!",
                style=wx.OK | wx.CENTRE | wx.ICON_ERROR
            )
            msgdlg.ShowModal()
        else:
            sequence = manifest.sequences[0]
            canvases = sequence.canvases

            progressstr = "Downloading Canvas {} of {}"
            progressdlg = wx.ProgressDialog(
                title="Downloading \"{}\"".format(manifest.label),
                message="Starting...",
                maximum=len(canvases),
                style=wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME
            )

            for canvas, num in zip(canvases, range(len(canvases))):
                ok, _ = progressdlg.Update(
                    num,
                    newmsg=progressstr.format(num + 1, len(canvases))
                )
                if not ok:
                    break
                runthread = Thread(
                    target=utils.download_canvas,
                    args=(canvas, path)
                )
                runthread.start()
                while runthread.is_alive():
                    progressdlg.Update(num)
                    runthread.join(0.200)

            progressdlg.Destroy()

        print("Pressed")


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()
