import logging
import numpy as np

from django.conf import settings
from django.db.models import QuerySet


def delete_chunks(qs: QuerySet,
                  logger: logging.Logger,
                  log_level = logging.INFO,
                  stepsize: int = settings.STEPSIZE):
    """delete entries from queryset in chunks using raw-delete sql"""
    model = qs.model
    model_name = model._meta.object_name
    logger.log(log_level, f'Suche zu löschende {model_name}-Einträge')
    ids = np.fromiter(qs.values_list('id', flat=True), np.dtype(np.int64))
    n_rows = ids.shape[0]
    if not n_rows:
        return
    if hasattr(model, 'remove_n_rels'):
        model.remove_n_rels(qs)
    logger.log(log_level, f'Lösche insgesamt {n_rows:n} {model_name}-Einträge')
    for i in np.arange(0, n_rows, stepsize, dtype=np.int64):
        chunk = ids[i:i + stepsize]
        qs_chunk = model.objects.filter(id__in=chunk)
        n_deleted = qs_chunk._raw_delete(using=qs_chunk.db)
        logger.log(log_level, f'{i + n_deleted:n}/{n_rows:n} {model_name}'
                   '-Einträgen gelöscht')
