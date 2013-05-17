from bsPlugins import *
from bbcflib.btrack import track
from bbcflib import genrep
from bbcflib.bFlatMajor.figure import genomeGraph
import os

meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'signals_plus', 'type': 'track', 'multiple': 'SigMultiP'},
                 {'id': 'signals_minus', 'type': 'track', 'multiple': 'SigMultiM'},
                 {'id': 'features', 'type': 'track', 'multiple': 'FeatMulti'},
                 {'id': 'assembly', 'type': 'assembly'}]
out_parameters = [{'id': 'genome_graph', 'type': 'pdf'}]

class GenomeGraphForm(BaseForm):
    class SigMultiP(twb.BsMultiple):
        label='Positive Signals: '
        signals_plus = twb.BsFileField(label=' ',
                                       help_text='Signal files (e.g. bedgraph) to plot above the axis',
                                       validator=twb.BsFileFieldValidator(required=True))
    class SigMultiM(twb.BsMultiple):
        label='Negative Signals: '
        signals_minus = twb.BsFileField(label=' ',
                                       help_text='Signal files (e.g. bedgraph) to plot below the axis',
                                       validator=twb.BsFileFieldValidator(required=True))
    class FeatMulti(twb.BsMultiple):
        label='Features: '
        features = twb.BsFileField(label=' ',
                                   help_text='Features files (e.g. bed) to plot as lines on the axis',
                                   validator=twb.BsFileFieldValidator(required=True))
    assembly = twf.SingleSelectField(label='Assembly: ',
                                     options=genrep.GenRep().assemblies_available(),
                                     prompt_text=None,
                                     help_text='Reference genome')
    submit = twf.SubmitButton(id="submit", value="Plot")


class GenomeGraphPlugin(BasePlugin):
    description = """Generates a whole genome overview of several signal and/or feature tracks."""
    info = {'title': 'Genome overview graph',
            'description': description,
            'path': ['Graphics', 'Genome graph'],
            'output': GenomeGraphForm,
            'in': in_parameters,
            'out': out_parameters,
            'meta': meta}

    def __call__(self, **kw):
        assembly = kw.get('assembly') or 'guess'
        signals_plus = kw.get('SigMultiP',{}).get('signals_plus', [])
        if not isinstance(signals_plus, list): signals_plus = [signals_plus]
        signals_minus = kw.get('SigMultiM',{}).get('signals_minus', [])
        if not isinstance(signals_minus, list): signals_minus = [signals_minus]
        features = kw.get('FeatMulti',{}).get('features', [])
        if not isinstance(features, list): features = [features]
        sptracks = [track(sig,chrmeta=assembly) for sig in signals_plus]
        smtracks = [track(sig,chrmeta=assembly) for sig in signals_minus]
        ftracks = [track(feat,chrmeta=assembly) for feat in features]
        snames = [t.name for t in signals_plus+signal_minus+features]
        if len(sptracks) > 0:
            chrmeta = sptracks[0].chrmeta
        elif len(smtracks) > 0:
            chrmeta = smtracks[0].chrmeta
        elif len(features) > 0:
            chrmeta = ftracks[0].chrmeta
        else:
            raise ValueError("No data provided")
        pdf = self.temporary_path(fname='genome_graph.pdf')
        genomeGraph(chrmeta,
                    [sig.read() for sig in sptracks],
                    [sig.read() for sig in smtracks],
                    [feat.read() for feat in ftracks],
                    output=pdf, new=new, last=True, legend=snames)
        self.new_file(pdf, 'genome_graph')
        return self.display_time()
