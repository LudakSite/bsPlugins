from bsPlugins import *
from bbcflib import genrep
from bbcflib.btrack import track
from bbcflib.bFlatMajor.common import score_threshold,apply
import math
import tw2.forms as twf
class NumericOperationForm(BaseForm):
    class SigMulti(twb.BsMultiple):
        label='Signals: '
        track = twb.BsFileField(label=' ',
            help_text='Select files (e.g. bedgraph)',
            validator=twb.BsFileFieldValidator(required=True))
    function =  twf.SingleSelectField(label='Operation: ',
        prompt_text=None,
        options=["log2","log10","sqrt"],
        validator=twc.Validator(required=False),
        help_text='Select a function')
    format = twf.SingleSelectField(label='Output format: ',
        prompt_text=None,
        options=["sql","bedgraph","bigwig","wig"],
        validator=twc.Validator(required=False),
        help_text='Output file(s) format, by default: same format as input file(s) format(s)')
    assembly = twf.SingleSelectField(label='Assembly: ',
        prompt_text=None,
        options=genrep.GenRep().assemblies_available(),
        help_text='Reference genome')
    submit = twf.SubmitButton(id="submit", value="Submit")


meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'track', 'type': 'track', 'required': True, 'multiple':'SigMulti'},
                {'id': 'assembly', 'type': 'assembly', 'required': True},
                {'id': 'function', 'type': 'function'},
                {'id': 'format', 'type': 'format'}]
out_parameters = [{'id': 'output', 'type': 'file'}]


class NumericOperationPlugin(BasePlugin):
    description = """Apply a numeric transformation to the track scores - such as logarithm or square root."""
    info = {
        'title': 'Numeric Operation',
        'description': description,
        'path': ['Signal', 'Numeric Operation'],
        'output': NumericOperationForm,
        'in': in_parameters,
        'out': out_parameters,
        'meta': meta,
        }
    def __call__(self, **kw):
        def filter_track(t):    # the function that is applied to the scores
            if kw['function']=="sqrt":
                return score_threshold(t, threshold=0, lower=False, strict=False, fields='score') # score >= 0
            else:
                return score_threshold(t, threshold=0, lower=False, strict=True, fields='score') # score > 0
        def method(x):    # the function that is applied to the scores
            if kw['function']=="log2":
                return math.log(x,2) ;
            elif kw['function']=="log10":
                return math.log(x,10) ;
            elif kw['function']=="sqrt":
                return math.sqrt(x) ;
        assembly = genrep.Assembly(kw.get('assembly'))
        l_track = kw.get('track', [])
        if not isinstance(l_track, list): l_track = [l_track]
        for tname in l_track :
            tinput = track(tname, chrmeta=kw.get('assembly'))
            (filepath, filename) = os.path.split(tname)
            (shortname, extension) = os.path.splitext(filename)
            if  "score" in tinput.fields:
                if kw['format']=="":
                    out_name = shortname+'_'+kw['function']+str(extension)
                else:
                    out_name = shortname+'_'+kw['function']+'.'+kw['format']
                output_name = self.temporary_path(out_name)
                out_track = track(output_name,chrmeta=assembly.chrmeta)
                out_track.write(apply(filter_track(tinput),'score',method), mode='write')
                out_track.close()
            tinput.close()
        return self.display_time()
