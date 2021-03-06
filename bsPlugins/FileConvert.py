from bsPlugins import *
from bbcflib.track import convert, _track_map
from bbcflib import genrep
import os

format_list = ['bedgraph', 'wig', 'bed', 'sql', 'gff', 'sga', 'bigwig']
to_map = {'sql': ['dtype', 'assembly'], 'bigwig': ['assembly']}
dtype_opts = ['quantitative', 'qualitative']

class FileConvertForm(BaseForm):
    hover_help = True
    show_errors = True
    infile = twb.BsFileField(label='File: ',
        help_text='Select file.',
        validator=twb.BsFileFieldValidator(required=True))
    child = twd.HidingTableLayout()
    to = twd.HidingSingleSelectField(label='Output format: ',
        options=format_list,
        prompt_text=None,
        mapping={'sql': ['dtype', 'assembly'],
                 'bigwig': ['assembly']},
        validator=twc.Validator(required=True),
        help_text='Select the format of your result')
    dtype = twf.SingleSelectField(label='Output datatype: ',
        prompt_text=None,
        options=['quantitative', 'qualitative'],
        help_text='Choose sql data type attribute')
    assembly = twf.SingleSelectField(label='Assembly: ',
        options=genrep.GenRep().assemblies_available(),
        help_text='Reference genome')
    submit = twf.SubmitButton(id="submit", value="Convert")


meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'infile', 'type': 'track', 'required': True, 'label': 'File: ', 'help_text': 'Select file'},
                 {'id': 'to', 'type': 'list', 'required': True, 'label': 'Output format: ', 'help_text': 'Select the format of your result', 'options': format_list, 'mapping': to_map, 'prompt_text': None },
                 {'id': 'dtype', 'type': 'list', 'label': 'Output datatype: ', 'help_text':'Choose sql data type attribute', 'options': dtype_opts, 'prompt_text':None},
                 {'id': 'assembly', 'type': 'assembly', 'label': 'Assembly: ', 'help_text': 'Reference genome', 'options': genrep.GenRep().assemblies_available()}]

out_parameters = [{'id': 'converted_file', 'type': 'track'}]


class FileConvertPlugin(BasePlugin):
    """Converts a file to another equivalent format (examples: wig to bedgraph, gff to bed). Recognised input formats are %s."""
    __doc__ %= ", ".join(sorted(_track_map.keys())[1:])
    info = {
        'title': 'File format conversion',
        'description': __doc__,
        'path': ['Files', 'Convert'],
#        'output': FileConvertForm,
        'in': in_parameters,
        'out': out_parameters,
        'meta': meta,
        }

    def __call__(self, **kw):
        ext = kw.get('to','sql')
        info = {'datatype': kw.get('datatype') or 'qualitative'}
        infile = kw.get('infile')
        fname = os.path.splitext(os.path.split(infile)[-1])[0]
        outfile = self.temporary_path(fname=fname, ext=ext)
        convert(infile, outfile,
                chrmeta=kw.get('assembly') or None, info=info)
        self.new_file(outfile, 'converted_file')
        return self.display_time()
