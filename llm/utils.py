import jinja2


def get_template_variables(template_str):
    """Get a list of expected variables from a Jinja template.

    Takes a Jinja template string and returns a list of variables expected to be
    provided when rendering the template.

    Args:
        template_str: str - A Jinja template string.

    Returns:
        set of str: The names of variables expected by the template.
    """
    env = jinja2.Environment()

    # https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.meta.find_undeclared_variables
    # Extract undeclared variables from the template AST
    parsed_template = env.parse(template_str)
    return jinja2.meta.find_undeclared_variables(parsed_template)
