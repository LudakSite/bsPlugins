from bsPlugins import *
from bbcflib.btrack import convert
from bbcflib import genrep
import os

format_list = ['bedgraph', 'wig', 'bed', 'sql', 'gff', 'sga', 'bigwig']


class FileConvertForm(BaseForm):
    hover_help = True
    show_errors = True
    infile = twf.FileField(label='File: ', help_text='Select file.',
        validator=twf.FileValidator(required=True))
    child = twd.HidingTableLayout()
    to = twd.HidingSingleSelectField(label='Output format: ',
        options=format_list,  prompt_text=None,
        mapping={'sql': ['dtype', 'assembly'],
                 'bigwig': ['assembly']},
        validator=twc.Validator(required=True),
        help_text='Select the format of your result')
    dtype = twf.SingleSelectField(label='Output datatype: ', prompt_text=None,
        options=['quantitative', 'qualitative'],
        help_text='Choose sql data type attribute')
    assembly = twf.SingleSelectField(label='Assembly: ',
        options=genrep.GenRep().assemblies_available(),
        help_text='Reference genome')
    submit = twf.SubmitButton(id="submit", value="Convert")


meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'infile', 'type': 'track', 'required': True},
                 {'id': 'to', 'type': 'list'},
                 {'id': 'dtype', 'type': 'list'},
                 {'id': 'assembly', 'type': 'assembly'}]

out_parameters = [{'id': 'converted_file', 'type': 'track'}]


class FileConvertPlugin(BasePlugin):
    info = {
        'title': 'Convert file',
        'description': 'Convert a file to a different format',
        'path': ['Files', 'Convert'],
        'output': FileConvertForm,
        'in': in_parameters,
        'out': out_parameters,
        'meta': meta,
        }

    def __call__(self, **kw):
        ext = kw.get('to') or 'sql'
        info = {'datatype': kw.get('datatype') or 'qualitative'}
        infile = kw.get('infile')
        fname = os.path.splitext(os.path.split(infile)[-1])[0]
        outfile = self.temporary_path(fname=fname, ext=ext)
        convert(infile, outfile,
                chrmeta=kw.get('assembly') or None, info=info)
        self.new_file(outfile, 'converted_file')
        return self.display_time()
