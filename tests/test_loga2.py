from unittest2 import TestCase, skip
from bsPlugins.loga2 import loga2Plugin
from bbcflib.btrack import track
import os
path = './testing_files/'
class Test_loga2Plugin(TestCase):
    def setUp(self):
        self.plugin = loga2Plugin()
    def test_with_signals(self):
        self.plugin(**{'track':[path+'CTCF_deconv.sql'],
        'assembly':'mm9', "format":"sql",'function':'sqrt'})
        #self.plugin(**{'track':[path+'test1.bedGraph',path+'CTCF_deconv.sql', path+'test2.bedGraph',path+"CTCF_rev.bw", path+'WT50.bedGraph', path+'KO50.bedGraph'],
        #'assembly':'mm9', "format":"",'function':'log2'})
    def tearDown(self):
        for f in os.listdir('.'):
            if f.startswith('tmp'):
                os.system("rm -rf %s" % f)
