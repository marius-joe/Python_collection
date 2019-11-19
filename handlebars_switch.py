#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Utilities for the HandleBars template engine
#  v0.2.1
# ******************************************

# Under Construction

"""Utilities for the HandleBars template engine"""

from typing import Any, List
import pybars

# final example:
# {{#each good.items}}
# {{#switch this.type}}
# {{#case '1'}}MATCH: {{this}}{{/case}}
# {{#default}}NOT MATCH{{/default}}
# {{/switch}}
# {{/each}}

# Register the statement in a map:
helpers = {
    "switch": switch,
    "case": case,
    "default": default
}

# use the statement in a template:
hbs = pybars.Compiler().compile(source=handlebars_template)
print(hbs(data, helpers=helpers))


def switch(scope, partials, value: object) -> Any:
    switch_values.append(SwitchEntry(switch_value=value))
    result = partials['fn'](scope)
    switch_values.pop()

    return result

def case(scope, partials, value: object) -> Any:
    if switch_values[-1].switch_value == value:
        switch_values[-1].matched = True
        return partials['fn'](scope)

def default(scope, partials) -> Any:
    if not switch_values[-1].matched:
        return partials['fn'](scope)

class SwitchEntry(object):
    """ A Switch entry that is executing in a handlebars template."""
    switch_value: Any
    matched: bool

    def __init__(self,
                 switch_value: Any,
                 matched: bool = False) -> None:
        self.switch_value = switch_value
        self.matched = matched

switch_values: List[SwitchEntry] = []

