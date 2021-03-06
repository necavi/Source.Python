# ../core/dumps.py

"""Provides dump logging functionalities."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
#   Inspect
from inspect import ismethod

# Source.Python Imports
#   Cvars
from cvars import cvar
from cvars.flags import ConVarFlags
#   Engines
from engines.server import server_game_dll
#   Entities
from entities.props import SendPropType
#   Memory
from memory import Pointer
from memory.helpers import MemberFunction
#   Paths
from paths import LOG_PATH
#   Stringtables
from stringtables import string_tables


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('dump_convars',
           'dump_server_classes',
           'dump_string_tables',
           'dump_weapon_scripts',
           )


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
_convar_types = {
    True: 'CMD',
    False: 'VAR',
}


# =============================================================================
# >> DUMP FUNCTIONS
# =============================================================================
def dump_convars(filename):
    """Dump all convars to the given filename."""
    # Create a dictionary to store the convars
    convars = dict()

    # Get the first convar
    convar = cvar.get_commands()

    # Loop through all convars
    while convar is not None:

        # Store the convar in the dictionary
        convars[convar.get_name()] = convar

        # Move to the next convar
        convar = convar.get_next()

    # Get the number of commands
    command_count = len([
        convar_name for convar_name in convars
        if convars[convar_name].is_command()])

    # Open/close the file
    with LOG_PATH.joinpath(filename + '.txt').open('w') as open_file:

        # Write the header
        open_file.write(
            'Commands: {0} - Variables: {1} - Total: {2}\n\n'.format(
                command_count, len(convars) - command_count, len(convars)))

        # Loop through all convars in alphabetic order
        for convar_name, convar in sorted(convars.items()):

            # Get the type (CMD/VAR) of convar
            convar_type = _convar_types[convars[convar_name].is_command()]

            # Get the convar's flags
            convar_flags = [
                flag.name for flag in ConVarFlags if flag & convar.get_flags()]

            # Get the convar's help text
            convar_text = convar.get_help_text()

            # Write the convar with its values to file
            open_file.write('{0} - {1}{2}\n{3}\n\n'.format(
                convar_name, convar_type,
                ' - (' + ','.join(convar_flags) + ')' if convar_flags else '',
                '\t' + convar_text if convar_text else ''))


def dump_server_classes(filename):
    """Dump all server class send properties to the given filename."""
    # Open/close the file
    with LOG_PATH.joinpath(filename + '.txt').open('w') as open_file:

        # Get the starting server class
        server_class = server_game_dll.get_all_server_classes()

        # Use a while statement to loop through all server classes
        while server_class:

            # Print the server class' name to file
            open_file.write('{0}\n'.format(server_class.name))

            # Get all items in the server class' table
            _dump_server_class_table(server_class.table, open_file)

            # Move to the next server class
            server_class = server_class.next

            # Was this not the last server class?
            if server_class is not None:

                # Write a separator line before the next server class output
                open_file.write('\n')


def dump_string_tables(filename):
    """Dump all string tables to the given filename."""
    # Open/close the file
    with LOG_PATH.joinpath(filename + '.txt').open('w') as open_file:

        # Loop through the string tables
        for current_index, string_table in enumerate(string_tables):

            # Is the current index not zero?
            if current_index:

                # If so, Write a separator line before the next string table
                open_file.write('\n')

            # Get a filtered list of the table's strings skipping all blank
            #   ones...
            items = list(filter(None, string_table))

            # Write the string table's name and length to file
            open_file.write('{0} (Length: {1})\n'.format(
                string_table.name, len(items)))

            # Loop through all items in the string table
            for item in items:

                # Write the item to file
                open_file.write('    {0}\n'.format(item))


def dump_weapon_scripts(filename):
    """Dump all WeaponInfo instances to the given file name."""
    # Import weapon_scripts
    # This was moved here due to issues with the bms branch
    from weapons.scripts import weapon_scripts

    # Open/close the file
    with LOG_PATH.joinpath(filename + '.txt').open('w') as open_file:

        # Loop through all WeaponInfo instances...
        for info in weapon_scripts:

            # Is the current script not parsed yet?
            if not info.is_script_parsed:

                # If so, skip the current weapon...
                continue

            # Write the current weapon class name...
            open_file.write('{0}\n'.format('=' * 80))
            open_file.write('{0}\n'.format(info.class_name))
            open_file.write('{0}\n'.format('=' * 80))

            # Loop through all WeaponInfo's attributes...
            for attr in dir(info):

                # Is the current attribute private or inherited from
                #   Pointer?
                if attr.startswith('_') or hasattr(Pointer, attr):

                    # If so, skip it...
                    continue

                # Get the current attribute value...
                value = getattr(info, attr)

                # Is the current attribute a method or inehrited from Pointer?
                if ismethod(value) or isinstance(
                        value, (MemberFunction, Pointer)):

                    # If so, skip it...
                    continue

                # Write the current attribute...
                open_file.write('{0} = {1}\n'.format(attr, value))


# =============================================================================
# >> HELPER FUNCTIONS
# =============================================================================
def _dump_server_class_table(table, open_file, level=1, offset=0):
    """Dump all items in the given table to the given file."""
    # Loop through the send props in the table
    for prop in table:

        # Skip all baseclasses
        if prop.name == 'baseclass':
            continue

        # Get the current offset in case this
        # property is inside an internal table
        new_offset = prop.offset + offset

        # Is the current prop a table?
        if prop.type == SendPropType.DATATABLE:

            # Get the new table's instance
            new_table = prop.get_data_table()

            # Was there an offset passed?
            if offset:

                # Write the property and its values to file
                open_file.write(
                    '{0}{1} {2} (offset {3} - {4}) [{5} properties]:\n'.format(
                        '    ' * level, prop.type, prop.name,
                        prop.offset, new_offset, len(new_table)))

            # Was no offset passed?
            else:

                # Write the property and its values to file
                open_file.write(
                    '{0}{1} {2} (offset {3}) [{4} properties]:\n'.format(
                        '    ' * level, prop.type, prop.name,
                        prop.offset, len(new_table)))

            # Dump all items in the table
            _dump_server_class_table(
                new_table, open_file, level + 1, new_offset)

        # Was there an offset passed?
        elif offset:

            # Write the property and its values to file
            open_file.write('{0}{1} {2} (offset {3} - {4})\n'.format(
                '    ' * level, prop.type, prop.name,
                prop.offset, prop.offset + offset))

        # Was no offset passed?
        else:

            # Write the property and its values to file
            open_file.write('{0}{1} {2} (offset {3})\n'.format(
                '    ' * level, prop.type, prop.name, prop.offset))
