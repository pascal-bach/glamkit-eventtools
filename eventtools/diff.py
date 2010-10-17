# -*- coding: utf-8 -*-
# from django-moderation.
# modified to include rather than exclude, fields
import re
import difflib


def get_changes_between_models(model1, model2, include=[]):
    from django.db.models import fields
    changes = {}
    for field_name in include:
        field = type(model1)._meta.get_field(field_name)
        value2 = unicode(getattr(model2, field_name))
        value1 = unicode(getattr(model1, field_name))
        if value1 != value2:
            changes[field.verbose_name] = (value1, value2)
    return changes


def get_diff(a, b):
    out = []
    sequence_matcher = difflib.SequenceMatcher(None, a, b)
    for opcode in sequence_matcher.get_opcodes():

        operation, start_a, end_a, start_b, end_b = opcode

        deleted = ''.join(a[start_a:end_a])
        inserted = ''.join(b[start_b:end_b])
        
        if operation == "replace":
            out.append('<del class="diff modified">%s</del>'\
                       '<ins class="diff modified">%s</ins>' % (deleted,
                                                                inserted))
        elif operation == "delete":
            out.append('<del class="diff">%s</del>' % deleted)
        elif operation == "insert":
            out.append('<ins class="diff">%s</ins>' % inserted)
        elif operation == "equal":
            out.append(inserted)

    return out


def html_diff(a, b):
    """Takes in strings a and b and returns a human-readable HTML diff."""

    a, b = html_to_list(a), html_to_list(b)
    diff = get_diff(a, b)

    return u"".join(diff)


def html_to_list(html):
    pattern = re.compile(r'&.*?;|(?:<[^<]*?>)|'\
                         '(?:\w[\w-]*[ ]*)|(?:<[^<]*?>)|'\
                         '(?:\s*[,\.\?]*)', re.UNICODE)

    return [''.join(element) for element in filter(None,
                                                   pattern.findall(html))]


def generate_diff(instance1, instance2, include=[]):
    from django.db.models import fields
    
    changes = get_changes_between_models(instance1, instance2, include)
    
    fields_diff = []

    for field_name in include:
        field = type(instance1)._meta.get_field(field_name)
        field_changes = changes.get(field.verbose_name, None)
        if field_changes:
            change1, change2 = field_changes
            if change1 != change2:
                diff = {'verbose_name': field.verbose_name, 'diff': html_diff(change1, change2)}
                fields_diff.append(diff)
    return fields_diff
