def dividir_en_chunks(seq, size):
    """Generador que divide la secuencia 'seq' en chunks del tamaño 'size'."""
    for pos in range(0, len(seq), size):
        yield seq[pos:pos + size]
