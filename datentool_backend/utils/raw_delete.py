import logging
import numpy as np
from django.db.models import QuerySet


def delete_chunks(qs: QuerySet,
                  logger: logging.Logger,
                  stepsize: int = 100000):
    """delete entries from queryset in chunks using raw-delete sql"""
    model = qs.model
    model_name = model._meta.object_name
    logger.info(f'Suche zu löschende {model_name}-Einträge')
    ids = np.fromiter(qs.values_list('id', flat=True), np.dtype(np.int64))
    n_rows = ids.shape[0]
    logger.info(f'Lösche insgesamt {n_rows:n} {model_name}-Einträge')
    for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
        chunk = ids[i:i + stepsize]
        qs_chunk = model.objects.filter(id__in=chunk)
        n_deleted = qs_chunk._raw_delete(using=qs_chunk.db)
        logger.info(f'{i + n_deleted:n}/{n_rows:n} {model_name}-Einträgen gelöscht')
