from Bio import SeqIO

def read_fasta(path):
    return [(rec.id, str(rec.seq)) for rec in SeqIO.parse(path, "fasta")]
