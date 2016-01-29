# -*- coding: utf-8 -*-
"""Module with base commands per entries."""
from ..exceptions import (
    DoesNotExistException, ArgumentRequiredException,
)
from ..storage.strategies import (
    RelatedSaveStrategy,
    RelatedGetStrategy,
)
from .mixins import GetRelationMixin, InstanceOpertionMixin
from .base import AbstractCommand


class DetailCommand(GetRelationMixin, InstanceOpertionMixin, AbstractCommand):
    """Command for operating with models by id or names."""

    save_strategy = RelatedSaveStrategy
    get_strategy = RelatedGetStrategy

    all_operations = {'delete', 'update', 'create'}
    allowed_operations = set()
    """Allowed operations for detail command.

    E.g. allowed_operations = {'delete', 'update', 'create'}
    """

    def __init__(self, *args, **kwargs):
        """Construct new detail command."""
        super(DetailCommand, self).__init__(*args, **kwargs)
        assert self.all_operations.intersection(self.allowed_operations)

    def update(self, parsed_args):
        """Handle update command.

        Get models from storage, parse args and update models.
        """
        if not parsed_args.entry:
            raise ArgumentRequiredException(
                'At least one ID or NAME are required.'
            )
        instances = self.get_objects(parsed_args.entry)
        for i in instances:
            self.update_instance(parsed_args, i)

    def delete(self, parsed_args):
        """Handle delete command.

        Get models from storage, delete models.
        """
        if not parsed_args.entry:
            raise ArgumentRequiredException(
                'At least one ID or NAME are required.'
            )
        instances = self.get_objects(parsed_args.entry)
        for i in instances:
            self.delete_instance(i)

    @property
    def is_allow_delete(self):
        """Check is command handle model deleting."""
        return 'delete' in self.allowed_operations

    @property
    def is_allow_update(self):
        """Check is command handle model updating."""
        return 'update' in self.allowed_operations

    @property
    def is_allow_create(self):
        """Check is command handle model creating."""
        return 'create' in self.allowed_operations

    def get_parser(self, prog_name):
        """Create command line argument parser.

        Use it to add extra options to argument parser.
        """
        parser = super(DetailCommand, self).get_parser(prog_name)
        if self.is_allow_delete:
            parser.add_argument(
                '-d', '--delete',
                action='store_true', help='Delete entries.'
            )
        if self.is_allow_create or self.is_allow_update:
            parser.add_argument(
                '-I', '--interactive', action='store_true',
                help='Enter to interactive mode.'
            )
            parser.add_argument(
                '-L', '--label', metavar='NAME',
                help="Entry's label in Serverauditor"
            )
        if self.is_allow_delete or self.is_allow_update:
            parser.add_argument(
                'entry', nargs='*', metavar='ID or NAME',
                help='Pass to edit exited entries.'
            )

        return parser

    def take_action(self, parsed_args):
        """Process CLI call."""
        if self.is_allow_delete and parsed_args.delete:
            self.delete(parsed_args)
        else:
            if self.is_allow_create and not parsed_args.entry:
                self.create(parsed_args)
            elif self.is_allow_update and parsed_args.entry:
                self.update(parsed_args)

    def get_objects(self, ids__names):
        """Get model list.

        Models will match id and label with passed ids__names list.
        """
        ids, names = self.parse_ids_names(ids__names)
        instances = self.storage.filter(
            self.model_class, any,
            **{'id.rcontains': ids, 'label.rcontains': names}
        )
        if not instances:
            raise DoesNotExistException("There aren't any instance.")
        return instances

    # pylint: disable=no-self-use
    def parse_ids_names(self, ids__names):
        """Parse ids__models list."""
        ids = [int(i) for i in ids__names if i.isdigit()]
        return ids, ids__names