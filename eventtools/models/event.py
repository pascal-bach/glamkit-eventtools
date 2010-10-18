from django.db import models
from django.db.models.base import ModelBase
from mptt.models import MPTTModel, MPTTModelBase
from django.db.models.fields import FieldDoesNotExist
from eventtools.utils.inheritingdefault import ModelInstanceAwareDefault
from django.db.models import Count

class EventQuerySet(models.query.QuerySet):
    def occurrences(self, *args, **kwargs):
        return self.model.Occurrence().objects.filter(event__in=self).filter(*args, **kwargs)
    
    def opening_occurrences(self):
        pks = []
        for e in self:
            try:
                pks.append(e.opening_occurrence().id)
            except AttributeError:
                pass
        return self.occurrences(pk__in=pks)
        
    def opening_before(self, date):
        return self.opening_occurrences().before(date).events()
    def opening_after(self, date):
        return self.opening_occurrences().after(date).events()
    def opening_between(self, d1, d2):
        return self.opening_occurrences().between(d1, d2).events()
    def opening_on(self, date):
        return self.opening_occurrences().on(date).events()

    def closing_occurrences(self):
        pks = []
        for e in self:
            try:
                pks.append(e.closing_occurrence().id)
            except AttributeError:
                pass
        return self.occurrences(pk__in=pks)
        
    def closing_before(self, date):
        return self.closing_occurrences().before(date).events()
    def closing_after(self, date):
        return self.closing_occurrences().after(date).events()
    def closing_between(self, d1, d2):
        return self.closing_occurrences().between(d1, d2).events()
    def closing_on(self, date):
        return self.closing_occurrences().on(date).events()

    def _with_relatives_having(self, relatives_fn, *args, **kwargs):
        """
        Return the set of items in self that have relatives matching a particular criteria.
        """
        match_ids = set()
        for obj in self:
            matches = relatives_fn(obj)
            if matches.count(): #weird bug where filter returns results on an empty qs!
                matches = matches.filter(*args, **kwargs)
                if matches.count():
                    match_ids.add(obj.id)
        return self.filter(id__in=match_ids)

    def with_children_having(self, *args, **kwargs):
        return self._with_relatives_having(lambda x: x.get_children(), *args, **kwargs)
        
    def with_descendants_having(self, *args, **kwargs):
        include_self = kwargs.pop('include_self', True)
        return self._with_relatives_having(lambda x: x.get_descendants(include_self=include_self), *args, **kwargs)

    def with_parent_having(self, *args, **kwargs):
        return self._with_relatives_having(lambda x: self.filter(id=x.parent_id), *args, **kwargs)

    def with_ancestors_having(self, *args, **kwargs):
        return self._with_relatives_having(lambda x: x.get_ancestors(), *args, **kwargs)

    def _without_relatives_having(self, relatives_fn, *args, **kwargs):
        """
        Return the set of items in self that have 0 relatives matching a particular criteria.
        """
        match_ids = set()
        for obj in self:
            matches = relatives_fn(obj)
            if matches.count(): #weird bug where filter returns results on an empty qs!
                matches = matches.filter(*args, **kwargs)
                if matches.count() == 0:
                    match_ids.add(obj.id)
            else: #no relatives => win
                    match_ids.add(obj.id)                
        return self.filter(id__in=match_ids)
        
    def without_children_having(self, *args, **kwargs):
        return self._without_relatives_having(lambda x: x.get_children(), *args, **kwargs)

    def without_descendants_having(self, *args, **kwargs):
        include_self = kwargs.pop('include_self', True)
        return self._without_relatives_having(lambda x: x.get_descendants(include_self=include_self), *args, **kwargs)

    def without_parent_having(self, *args, **kwargs):
        return self._without_relatives_having(lambda x: self.filter(id=x.parent_id), *args, **kwargs)

    def without_ancestors_having(self, *args, **kwargs):
        return self._without_relatives_having(lambda x: x.get_ancestors(), *args, **kwargs)
        
    #some simple annotations
    def having_occurrences(self):
        return self.annotate(num_occurrences=Count('occurrences')).filter(num_occurrences__gt=0)

    def having_n_occurrences(self, n):
        return self.annotate(num_occurrences=Count('occurrences')).filter(num_occurrences=n)

    def having_no_occurrences(self):
        return self.having_n_occurrences(0)
        
    def highest_having_occurrences(self):
        """
        the highest objects that have occurrences meet these conditions:
            a) they have occurrences
            b) none of their ancestors have occurrences
        
        This is a good first blush at 'The List Of Events', since it is the longest list of events whose descendants'
        occurrences will cover the entire set of occurrences with no repetitions.
        """
        return self.having_occurrences()._without_relatives_having(
            lambda x: x.get_ancestors().annotate(num_occurrences=Count('occurrences')),
            num_occurrences__gt=0
        )


class EventManager(models.Manager):
    def get_query_set(self): 
        return EventQuerySet(self.model)
        
    def occurrences(self, *args, **kwargs):
        return self.get_query_set().occurrences(*args, **kwargs)

    def opening_before(self, *args, **kwargs):
        return self.get_query_set().opening_before(*args, **kwargs)
    def opening_after(self, *args, **kwargs):
        return self.get_query_set().opening_after(*args, **kwargs)
    def opening_between(self, *args, **kwargs):
        return self.get_query_set().opening_between(*args, **kwargs)
    def opening_on(self, *args, **kwargs):
        return self.get_query_set().opening_on(*args, **kwargs)
    def closing_before(self, *args, **kwargs):
        return self.get_query_set().closing_before(*args, **kwargs)
    def closing_after(self, *args, **kwargs):
        return self.get_query_set().closing_after(*args, **kwargs)
    def closing_between(self, *args, **kwargs):
        return self.get_query_set().closing_between(*args, **kwargs)
    def closing_on(self, *args, **kwargs):
        return self.get_query_set().closing_on(*args, **kwargs)        
    def with_children_having(self, *args, **kwargs):
        return self.get_query_set().with_children_having(*args, **kwargs)        
    def with_descendants_having(self, *args, **kwargs):
        return self.get_query_set().with_descendants_having(*args, **kwargs)        
    def with_parent_having(self, *args, **kwargs):
        return self.get_query_set().with_parent_having(*args, **kwargs)        
    def with_ancestors_having(self, *args, **kwargs):
        return self.get_query_set().with_ancestors_having(*args, **kwargs)        
    def without_children_having(self, *args, **kwargs):
        return self.get_query_set().without_children_having(*args, **kwargs)        
    def without_descendants_having(self, *args, **kwargs):
        return self.get_query_set().without_descendants_having(*args, **kwargs)        
    def without_parent_having(self, *args, **kwargs):
        return self.get_query_set().without_parent_having(*args, **kwargs)        
    def without_ancestors_having(self, *args, **kwargs):
        return self.get_query_set().without_ancestors_having(*args, **kwargs)        
    def having_occurrences(self):
        return self.get_query_set().having_occurrences()        
    def having_n_occurrences(self, n):
        return self.get_query_set().having_n_occurrences(n)        
    def having_no_occurrences(self):
        return self.get_query_set().having_no_occurrences()        
    def highest_having_occurrences(self):
        return self.get_query_set().highest_having_occurrences()        
            
class EventOptions(object):
    """
    Options class for Event models. Use this as an inner class called EventMeta:
    
    class MyModel(EventModel):
        class EventMeta:
            fields_to_inherit = ['name', 'slug', 'description']
        ...     
    """
    
    fields_to_inherit = []
    
    def __init__(self, opts):
        # Override defaults with options provided
        if opts:
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)


class EventModelBase(MPTTModelBase):
    def __new__(meta, class_name, bases, class_dict):
        """
        Create subclasses of MPTTModel. This:
         - adds the MPTT fields to the class
         - adds a TreeManager to the model
        """
        event_opts = class_dict.pop('EventMeta', None)
        class_dict['_event_meta'] = EventOptions(event_opts)
        cls = super(EventModelBase, meta).__new__(meta, class_name, bases, class_dict)
                
        try:
            EventModel
        except NameError:
            # We're defining the base class right now, so don't do anything
            # We only want to add this stuff to the subclasses.
            # (Otherwise if field names are customized, we'll end up adding two
            # copies)
            pass
        else:
            for field_name in class_dict['_event_meta'].fields_to_inherit:
                try:
                    field = cls._meta.get_field(field_name)
                    #injecting our fancy inheriting default
                    field.default = ModelInstanceAwareDefault(field_name, field.default)
                except models.FieldDoesNotExist:
                    continue
                
            # for key in ('left_attr', 'right_attr', 'tree_id_attr', 'level_attr'):
            #     field_name = getattr(cls._mptt_meta, key)
            #     try:
            #         cls._meta.get_field(field_name)
            #     except models.FieldDoesNotExist:
            #         field = models.PositiveIntegerField(db_index=True, editable=False)
            #         field.contribute_to_class(cls, field_name)
            pass
        return cls


class EventModel(MPTTModel):
    __metaclass__ = EventModelBase
    
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    objects = EventManager()

    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        self.cascade_changes_to_children()
        return super(EventModel, self).save(*args, **kwargs)
                
    @classmethod
    def Occurrence(cls):
        return cls.occurrences.related.model
        
    def reload(self):
        """
        Call with x = x.reload() - it doesn't change itself
        """
        return type(self).objects.get(pk=self.pk)
        
    def cascade_changes_to_children(self):
        if self.pk:
            saved_self = type(self).objects.get(pk=self.pk)
            attribs = type(self)._event_meta.fields_to_inherit
        
            for child in self.get_children():
                for a in attribs:
                    try:
                        saved_value = getattr(saved_self, a)
                        ch_value = getattr(child, a)
                        if ch_value == saved_value: #the child inherits this value from the parent
                            new_value = getattr(self, a)
                            setattr(child, a, new_value)
                    except AttributeError:
                        continue
                child.save() #cascades to grandchildren
                
    def has_occurrences(self):
        return self.occurrences.count()
        
    def opening_occurrence(self):
        try:
            return self.occurrences.all()[0]
        except IndexError:
            return None
        
    def closing_occurrence(self):
        try:
            return self.occurrences.all().reverse()[0]
        except IndexError:
            return None

    def get_descendants(self, include_self=True):
        descendantsqs = super(EventModel, self).get_descendants(include_self=include_self)
        # it's a django QuerySet, so we need to recast it as an EventQuerySet to call occurrences() on it.
        return descendantsqs._clone(klass=EventQuerySet)

    def get_family(self, include_self=True):
        familyqs = self.get_ancestors() | super(EventModel, self).get_descendants(include_self=include_self)
        # it's a django QuerySet, so we need to recast it as an EventQuerySet to call occurrences() on it.
        return familyqs._clone(klass=EventQuerySet)