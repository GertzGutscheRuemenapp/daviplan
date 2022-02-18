import sys
import logging
logger = logging.getLogger(__name__)

from postgres_copy import CopyQuerySet
from postgres_copy.copy_from import CopyMapping
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import connection, models
from django.db.transaction import TransactionManagementError



class DirectCopyMapping(CopyMapping):
    """Direct CopyMapping"""
    def save(self, silent=False, stream=sys.stdout):
        """
        Saves the contents of the CSV file to the database.

        Override this method and use 'self.create(cursor)`,
        `self.copy(cursor)`, `self.insert(cursor)`, and `self.drop(cursor)`
        if you need functionality other than the default create/copy/insert/drop
        workflow.

         silent:
           By default, non-fatal error notifications are printed to stdout,
           but this keyword may be set to disable these notifications.

         stream:
           Status information will be written to this file handle. Defaults to
           using `sys.stdout`, but any object with a `write` method is
           supported.
        """
        logger.debug("Loading CSV to {}".format(self.model.__name__))
        if not silent:
            stream.write("Loading CSV to {}\n".format(self.model.__name__))

        # Connect to the database
        with self.conn.cursor() as c:
            self.copy(c)

        if not silent:
            stream.write("{} records loaded\n".format(intcomma(self.insert_count)))

        return self.insert_count

    def pre_copy(self, cursor):
        """copy directy into target table"""
        self.temp_table_name = self.model._meta.db_table

    def post_copy(self, cursor):
        self.insert_count = cursor.rowcount
        #  reset temp tablename
        self.temp_table_name = "temp_%s" % self.model._meta.db_table


class DirectCopyQuerySet(CopyQuerySet):
    """a queryset that copies the data directly, without temp table"""

    def from_csv(self,
                 csv_path,
                 mapping=None,
                 drop_constraints=True,
                 drop_indexes=True,
                 silent=True,
                 direct_copy=True,
                 **kwargs):
        """
        Copy CSV file from the provided path to the current model using the provided mapping.
        """
        # Dropping constraints or indices will fail with an opaque error for all but
        # very trivial databases which wouldn't benefit from this optimization anyway.
        # So, we prevent the user from even trying to avoid confusion.
        if drop_constraints or drop_indexes:
            try:
                connection.validate_no_atomic_block()
            except TransactionManagementError:
                raise TransactionManagementError("You are attempting to drop constraints or "
                                                 "indexes inside a transaction block, which is "
                                                 "very likely to fail.  If it doesn't fail, you "
                                                 "wouldn't gain any significant benefit from it "
                                                 "anyway.  Either remove the transaction block, or set "
                                                 "drop_constraints=False and drop_indexes=False.")

        if direct_copy:
            mapping = DirectCopyMapping(self.model, csv_path, mapping, **kwargs)
        else:
            mapping = CopyMapping(self.model, csv_path, mapping, **kwargs)

        if drop_constraints:
            self.drop_constraints()
        if drop_indexes:
            self.drop_indexes()

        insert_count = mapping.save(silent=silent)

        if drop_constraints:
            self.restore_constraints()
        if drop_indexes:
            self.restore_indexes()

        return insert_count


DirectCopyManager = models.Manager.from_queryset(DirectCopyQuerySet)
