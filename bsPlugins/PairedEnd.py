from bsPlugins import *
from bbcflib.btrack import track
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri as numpy2ri
import os, tarfile

meta = {'version': "1.0.0",
        'author': "BBCF",
        'contact': "webmaster-bbcf@epfl.ch"}

in_parameters = [{'id': 'bamfiles', 'type': 'bam', 'required': True, 
                  'multiple': 'BamMulti'},
                 {'id': 'format', 'type': 'text'}]

out_parameters = [{'id': 'statistics_plot', 'type': 'pdf'},
                  {'id': 'fragment_track', 'type': 'track'},
                  {'id': 'fragment_track_tar', 'type': 'file'}]


class PairedEndForm(BaseForm):
    child = twd.HidingTableLayout()
    class BamMulti(twb.BsMultiple):
        label='Paired-end BAM files: '
        bamfiles = twb.BsFileField(label=' ',
                                   help_text='Select bam files',
                                   validator=twb.BsFileFieldValidator(required=True))
    format = twf.SingleSelectField(label='Output format: ',
                                   options=["sql", "bedGraph", "bigWig"],
                                   prompt_text=None,
                                   help_text='Format of the output file')
    submit = twf.SubmitButton(id="submit", value="Analyze")


class PairedEndPlugin(BasePlugin):
    """Computes statistics and genome-wide distribution of fragment sizes from mapped paired-end reads."""

    info = {
        'title': 'Analysis of fragment size in paired-end bam files.',
        'description': __doc__,
        'path': ['Analysis', 'Paired-end analysis'],
        'output': PairedEndForm,
        'in': in_parameters,
        'out': out_parameters,
        'meta': meta }

    def _compute_stats(self, bam, frag_rep, frag_size, nb_frag):
        _plast = -1
        _buff = {}
        for read in bam:
            if read.is_reverse: continue
            nb_frag += 1
            _p = read.pos
            _s = read.isize
            if _p == _plast:
                _buff[_s] = _buff.get(_s,0)+1
            else:
                for _size,_rep in _buff.iteritems():
                    frag_size[_size] = frag_size.get(_size,0)+_rep
                    frag_rep[_rep] = frag_rep.get(_rep,0)+1
                _plast = _p
                _buff = {}
        for _rep in _buff.values():
            frag_rep[_rep] = 1+frag_rep.get(_rep,0)
        return frag_rep, frag_size, nb_frag

    def _plot_stats(self, frag_rep, frag_size, nb_frag, bam_name):
        robjects.r.assign('rep_cnt',numpy2ri.numpy2ri(frag_rep.keys()))
        robjects.r.assign('rep_freq',numpy2ri.numpy2ri(frag_rep.values()))
        robjects.r.assign('size_distr',numpy2ri.numpy2ri(frag_size.keys()))
        robjects.r.assign('size_freq',numpy2ri.numpy2ri(frag_size.values()))
        robjects.r.assign('nb_frag',nb_frag)
        robjects.r.assign('main',bam_name)
        robjects.r("""
rep_cnt = as.integer(rep_cnt)
Od = order(rep_cnt)
rep_freq = as.integer(rep_freq)[Od]*1e-6
rep_cnt = rep_cnt[Od]
I100 = rep_cnt<100
rep_cnt = c(rep_cnt[I100],100)
rep_freq = c(rep_freq[I100],sum(rep_freq[!I100]))
size_distr = as.integer(size_distr)
Od = order(size_distr)
size_freq = as.integer(size_freq)[Od]*1e-6
size_distr = size_distr[Od]
par(mfrow=c(2,1),lwd=2,cex=1.1,cex.main=1.3,cex.lab=1.1,cex.axis=.8,oma=c(0,0,3,0),mar=c(5,5,1,1),las=1,pch=20)
plot(rep_cnt,rep_freq,type='s',main='Fragment redundancy',xlab='Nb of copies',ylab='Frequency (millions)',
     log='y',xlim=c(1,100),xaxt='n',ylim=c(0,nb_frag*1e-6)+1)
abline(h=nb_frag*1e-6,col='red')
text(50,nb_frag*1e-6,nb_frag,col='red',pos=1)
axis(side=1,at=seq(10,100,by=10),labels=c(seq(10,90,by=10),">100"))
plot(size_distr,size_freq,type='s',main='Fragment size distribution',xlab='Size',ylab='Frequency (millions)',ylim=c(0,nb_frag*1e-6)+1)
abline(h=nb_frag*1e-6,col='red')
text(mean(range(size_distr)),nb_frag*1e-6,nb_frag,col='red',pos=1)
title(main=main,outer=T)
""")


    def __call__(self, **kw):
        _f = ['start','end','score']
        format = kw.get("format") or "sql"
        bamfiles = kw.get('BamMulti',{}).get('bamfiles',[])
        if not isinstance(bamfiles, (tuple,list)): bamfiles = [bamfiles]
        bamfiles = [track(bam) for bam in bamfiles]
        all_tracks = []
        pdf = self.temporary_path(fname='Paired_end_plots.pdf')
        robjects.r('pdf("%s",paper="a4",height=11,width=8)' %pdf)
        for bam in bamfiles:
            tname = "%s_frags.%s" %(bam.name, format)
            outname = self.temporary_path(fname=tname)
            all_tracks.append(outname)
            trout = track(outname, fields=_f, chrmeta=bam.chrmeta)
            frag_rep = {}
            frag_size = {}
            nb_frag = 0
            for chrom,cval in bam.chrmeta.iteritems():
                reads = bam.fetch(chrom, 0, cval['length'])
                frag_rep, frag_size, nb_frag = self._compute_stats(reads, frag_rep, frag_size, nb_frag)
                trout.write( bam.PE_fragment_size(chrom), fields=_f, chrom=chrom )
            trout.close()
            self._plot_stats(frag_rep, frag_size, nb_frag, bam.name)
        robjects.r('dev.off()')
        if len(all_tracks)>1:
            tarname = self.temporary_path(fname='PE_fragment_tracks.tgz')
            tar_tracks = tarfile.open(tarname, "w:gz")
            [tar_tracks.add(f,arcname=os.path.basename(f)) for f in all_tracks]
            tar_tracks.close()
            self.new_file(tar_tracks, 'fragment_track_tar')
        else:
            self.new_file(all_tracks[0], 'fragment_track')
        self.new_file(pdf,'statistics_plot')
        return self.display_time()

