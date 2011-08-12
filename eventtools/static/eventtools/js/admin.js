(function($) {

	$(document).ready(function() {
		/*
		
		a workaround that allows inlines replace elements specified by a fieldset. Add something like this to your ModelAdmin fieldsets:
		
        ("OCCURRENCES_PLACEHOLDER", {
            'fields': (),
            'classes': ('occurrences-group',),
        }),

		where 'occurrences-group' is the id of the inline you want to replace it with.
		
		*/
		
		$(".inline-group").each(function() {
			var $this = $(this);
			var id = $this.attr('id');
			$("fieldset."+id).replaceWith($this);
		});
		
	});
})(jQuery);