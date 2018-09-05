import os
from econtools.metrics.core import Results
from econtools.util.gentools import force_iterable

eol = " \\\\ \n"
sig_labels = {1: '', .1: '*', .05: '**', .01: '***'}


# TODO: Allow empty `var_names` to mean 'grab all'
# TODO: Allow empty `var_labels` to mean 'just use default gross var_names'
# TODO: Add options for basic statrow (r2, N)? (how to handle 2sls r2?)
def outreg(regs, var_names=None, var_labels=None, digits=4, stars=True, se="(",
           options=False):
    """Create the guts of a Latex tabular enviornment from regression results.

    Args:
        regs (Results or iterable of Results): Regressions to output to table.
        var_names (str or iterable of str): Variable names to pull from regs.
            If none specified, by default uses the pandas dataframe colum names.
        var_labels (str or iterable of str): Pretty names for variables in
            table. If none specified, will use var_names
    Keyword Args:
        digits (int): Defaults to 4. How many digits to include past decimal.
        stars (bool): Defaults to True. If True, adds stars to mark statistical
            significance.
        se (str): Defaults to "(". Marker for standard errors. May
            also choose brackets with ``se="["``.
        options (bool): Default to False: If True, return a ``dict`` with
            formatting options that were generated by ``outreg``:
            ``name_just``, ``stat_just``, etc., for additional calls to
            ``table_mainrow`` and ``table_statrow``.
    Return:
        str: LaTeX fragment meant to be wrapped in a tabular environment.
    """

    regs = force_iterable(regs)

    if var_names is None:
        var_names = []
        var_names = [var_names + list(reg.beta.index) for reg in regs]

    if var_labels is None:
        var_labels = [x for x in var_names if type(x) is str else str(x)]
    
    opt_dict = _set_options(var_labels, digits, stars)
    table_str = ''
    for var_idx, varname in enumerate(var_names):
        table_str += table_mainrow(var_labels[var_idx], varname, regs,
                                   **opt_dict)

    if options:
        return table_str, opt_dict
    else:
        return table_str

def _set_options(var_labels, digits, stars):
    label_lens = [len(label) for label in var_labels]
    name_just = max(label_lens) + 2
    stat_just = (
        digits +
        3 +     # Leading zero, decimal, negative sign
        3 +     # Stars
        4       # Extra buffer
    )
    opt_dict = {
        'name_just': name_just,
        'stat_just': stat_just,
        'digits': digits,
        'stars': stars,
    }
    return opt_dict


def table_mainrow(rowname, varname, regs,
                  name_just=24, stat_just=12, digits=3, se="(",
                  stars=True):

    """Add a table row of regression coefficients with standard errors.

    Args:
        rowname (str): First cell of table row, i.e., the row's name.
        varname (str): Name of variable to pull from ``Results`` object.
        regs (Results or iterable of Results): Regressions from which
          to pull coefficients named ``varname``.

    Keyword Args:
        name_just (int):
        stat_just (int):
        digits (int):
        se (str):
        stars (bool):

    Returns:
        str: String of table row.
    """

    # Start beta and SE rows
    beta_vals = []
    se_vals = []
    # Extract beta/sig and se values to pass to `table_statrow`
    for reg in force_iterable(regs):
        if type(reg) is not Results or varname not in reg.beta:
            beta_vals.append('')
            se_vals.append('')
        else:
            # Beta and stars
            this_beta = _format_nums(reg.beta[varname], digits=digits)
            if stars:
                this_sig = _sig_level(reg.pt[varname])
            else:
                this_sig = ''
            beta_vals.append(this_beta + this_sig)
            # Standard Error
            this_se = reg.se[varname]
            se_vals.append(this_se)

    beta_row = table_statrow(rowname, beta_vals, name_just=name_just,
                             stat_just=stat_just)
    se_row = table_statrow('', se_vals, name_just=name_just,
                           stat_just=stat_just, sd=se, digits=digits)

    full_row = beta_row + se_row

    return full_row


def table_statrow(rowname, vals, name_just=24, stat_just=12, wrapnum=False,
                  sd=False, digits=None,
                  empty_left=0, empty_right=0, empty_slots=[],
                  **kwargs):
    """Make a table row. Useful for bottom rows of regression tables
    (e.g., R-squared) or tables of summary statistics.

    Args:
        rowname (str): Row's name.
        vals (iterable): Values to fill cell rows. Can add empty cells with
            ``''``.

    Keyword Args:
        name_just (int): Width/justification of the ``rowname`` column.
        stat_just (int): Width/justification of the ``vals`` columns.
        wrapnum (bool): If True, wrap cell values in LaTeX function ``num``,
            which automatically adds commas as needed. Requires LaTeX package
            ``siunitx`` in LaTeX document.
        sd (bool or str): If True, wrap cell value in parentheses as per
            convention. May also set ``sd="["`` to wrap in brackets.
        digits (int): How many digits to print after decimal. If ``None``,
            prints contents of ``vals`` exactly as is.
        empty_left (int): Adds `empty_left` empty cells to left side of row.
          Is mutually exclusive with ``empty_slots``.
        empty_right (int): See ``empty_left``.
        empty_slots (list): Make table row have empty cells at index values
            in ``empty_slots`` (zero-indexed). Mutually exclusive with
            ``empty_left`` and ``empty_right``. For example, passing ``vals=(1,
            2, 3)`` and ``empty_slots=(1, 3, 5)`` is the same as passing
            ``vals=(1, '', 2, '', 3, '')``.

    Returns:
        str: LaTeX tabular row with ``rowname`` and ``vals`` with the
        specified formatting.

    Example:
        .. code-block:: python

            >>> table_str = table_statrow("Method", ['OLS', '2SLS', 'LIML'])
            >>> table_str += table_statrow("N", [100, 200, 300])
            >>> print(table_str)
            Method      & OLS   & 2SLS   & LIML  \\\\
            N           & 100   & 200    & 300   \\\\
    """

    outstr = rowname.ljust(name_just)

    cell = "\\num{{{}}}" if wrapnum else "{}"
    cell = _add_sd_parens(sd, cell)
    cell = "& " + cell

    vals = _add_filler_empty_cells(vals, empty_left, empty_right, empty_slots)

    for val in vals:
        # If empty string, add empty cell here (can't pass to `_format_nums` or
        # will get empty parens instead).
        if type(val) is str and len(val) == 0:
            outstr += "& ".ljust(stat_just)
        else:
            val_to_digits = (
                val if digits is None else _format_nums(val, digits=digits)
            )
            outstr += cell.format(val_to_digits).ljust(stat_just)

    outstr += eol

    return outstr

def _add_sd_parens(sd, cell):
    """ Wrap table cell in parens/brackets if needed """
    # Make `sd=True` same as `sd='('`
    if sd is True:
        sd = "("

    if type(sd) is str:
        # If `sd` is str, check if valid, then wrap `cell`
        if sd in ('(', '['):
            leftp = sd
            rightp = ")" if leftp == '(' else ']'
            cell = leftp + cell + rightp
        else:
            err_str = "Input '{}' invalid".format(sd)
            raise ValueError(err_str)
    elif sd is False:
        # If `sd` False, do nothing
        pass
    else:
        raise ValueError("Value `sd={}` invalid.".format(sd))

    return cell

def _add_filler_empty_cells(vals, empty_left, empty_right, empty_slots):
    # Convert left/right empty counts to list of empty slots
    if not (empty_left or empty_right or empty_slots):
        return vals
    elif (empty_left or empty_right) and empty_slots:
        raise ValueError("Cannot specify left/right empty and `empty_slots`.")
    elif not empty_slots:
        len_vals = len(vals)
        empty_slots = (
            list(range(empty_left)) +
            list(range(empty_left + len_vals,
                       empty_left + len_vals + empty_right))
        )

    # Add empty string to `vals` where appropriate
    new_vals = []
    nonempty_col = 0
    for i in range(len(vals) + len(empty_slots)):
        if i in empty_slots:
            new_vals.append('')
        else:
            new_vals.append(vals[nonempty_col])
            nonempty_col += 1

    return tuple(new_vals)


def _format_nums(x, digits=3):
    if type(x) is str:
        return x
    else:
        return '{{:.{}f}}'.format(digits).format(x)


# TODO: Make this adaptive
def _sig_level(p):
    if p > .1:
        p_level = 1
    elif .05 < p <= .1:
        p_level = .1
    elif .01 < p <= .05:
        p_level = .05
    else:
        p_level = .01

    return sig_labels[p_level]


def write_notes(notes, table_path):
    """Write notes for a table.

    Args:
        notes (str): String to write to disk.
        table_path (str): The filepath of the accompanying LaTeX table.

    Returns:
        None: Writes ``notes`` to ``<table_path_root>_notes.tex``. So if
        ``table_path=table_1.tex``, ``notes`` will be written to
        ``table_1_notes.tex``.

    Example:
        .. code-block:: python

            table_path = 'table_1.tex'
            notes = "Sample size is 277."
            write_notes(notes, table_path)
            # str ``notes`` written to ``table_1_notes.tex``
    """
    split_path = os.path.splitext(table_path)
    notes_path = split_path[0] + '_notes.tex'
    with open(notes_path, 'w') as f:
        f.write(notes)
