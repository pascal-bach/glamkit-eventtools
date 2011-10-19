(function($) {
	$(document).ready(function() {
				
		// make calendars scrollable
		var $el = $(".calendarlist .scrollable")
		$el.scrollable();
		
		// if the current month is in the list of scrollable items, scroll to it.
		var api = $el.data("scrollable");
		var today = new Date()
		function pad(n){return n<10 ? '0'+n : n}
		var month_str = today.getUTCFullYear()+'-'
			+ pad(today.getUTCMonth()+1);

		var offset = 0;
		api.getItems().each(function() {
			var $this = $(this);
			if ($this.attr("data") == month_str) {
				api.move(offset, 0)
				return false
			}	
			offset += 1;
		});
		
		var days_count = 	$("#sessions dt").size();
		
		if (days_count > 1) {
			//Hide sessions
			$("#sessions dt").hide();
			$("#sessions dd").hide();

			//inject an info/results box
			$("#sessions").prepend("<p class='help'>Click on calendar to see session times</p>");
		
			// Make highlighted dates look clickable
			$(".calendar td.highlight").css("cursor", "pointer");
		
			// Show session data when we click on a date
			$(".calendar td.highlight").click(function() {
				var $this = $(this);
				$(".calendar td.highlight").removeClass("clicked");
				$this.addClass("clicked");
				$("#sessions .help").hide();
				$("#sessions dt").hide();
				$("#sessions dd").hide();
				// show only the sessions with the data
				$("#sessions [data=\""+$this.attr('data')+"\"]").fadeIn(400);
			
			});
		} // endif 
	});

})(jQuery);