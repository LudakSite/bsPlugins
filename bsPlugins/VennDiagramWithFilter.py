from bsPlugins import *
from bbcflib.track import track
from bbcflib import genrep
from bbcflib.gfminer.figure import venn
from itertools import combinations
import os, re

meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'table', 'type': 'txt', 'required': True},
                {'id': 'id_columns', 'type': 'text', 'required': True},
                {'id': 'filters', 'type': 'text', 'required': True},
                {'id': 'format', 'type': 'format'}]

out_parameters = [{'id':'venn_diagram', 'type':'file'}]


class VennDiagramWithFilterForm(BaseForm):
    table = twb.BsFileField(label='table: ',
                            help_text='Select table',
                            validator=twb.BsFileFieldValidator(required=True))
    id_columns = twf.TextField(label='columns id: ',
                               validator=twc.Validator(required=True),
                               value='',
                               help_text='comma separated list of columns id for which Venn diagram will be generated (e.g. 3,5)')
    filters = twf.TextField(label='filters: ',
                            validator=twc.Validator(required=True),
                            value='',
                            help_text='comma separated list of simple filters which will be applied to each corresponding column id before doing the Venn diagram (e.g. >2,<0.05,>=2 OR <=-2,>=-2 AND <2,==2,!=2) - one filter per column should be given - leave an empty string if no filter should be applied to a given column (e.g., >2,,<0.05)')
    format = twf.SingleSelectField(label='Output format: ',
                                   options=["png","pdf"],
                                   prompt_text=None,
                                   validator=twc.Validator(required=False),
                                   help_text='Output figure format')
    submit = twf.SubmitButton(id="submit", value="Submit")


class VennDiagramWithFilterPlugin(BasePlugin):
    """Creates a Venn diagram of a table preliminarly filtered on given columns."""
    info = {
        'title': 'Venn Diagram With Filter',
        'description': __doc__,
        'path': ['Graphics', 'Venn Diagram With Filter'],
        'output': VennDiagramWithFilterForm,
        'in': in_parameters,
        'out': out_parameters,
        'meta': meta,
        }

    def __call__(self, **kw):

        def _parse_logic(string):
            s = re.sub(r'[^\w\d!=><\. ]', '', string)
            s = re.sub(r' OR ', ')or(%f ', s)
            s = re.sub(r' AND ', ')and(%f ', s)
            return "(%f "+s+")"

        s_cols = kw.get('id_columns','')
        s_filters = kw.get('filters','')
        format = kw.get('format','pdf')

        infile = track(kw.get('table',''),format='txt',header=True)
        col_ind = [int(i)-1 for i in s_cols.split(",")]
        colnames = [infile.header[i] if i<len(infile.header) else str(i) for i in col_ind]
        conds = [_parse_logic(x) for x in s_filters.split(",")]
        tlabels = [chr(k+65) for k in range(length(col_ind))]
        conds += ["1"]*(len(col_ind)-len(conds))
        combn = [sorted(x) for k in range(len(tlabels)) for x in combinations(tlabels,k+1)]
        c2 = dict(("|".join(c),0) for c in combn)
        indx = dict((c,[tlabels.index(x) for x in c]) for c in combn)

        for row in infile:
            tests = [eval(c % ((row[col_ind[i]],)*c.count("%f"))) for i,c in enumerate(conds)]
            for c in combn:
                c2["|".join(c)] += all([tests[i] for i in indx[c]])

        output = self.temporary_path(fname='venn_diagram.'+format)
        venn(c2,output=output,legend=colnames,format=format)
        self.new_file(output, 'venn_diagram')

        return self.display_time()


