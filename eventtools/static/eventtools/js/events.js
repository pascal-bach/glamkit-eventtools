(function($) {
	$(document).ready(function() {
				
		// make calendars scrollable
		var $el = $(".calendarlist .scrollable")
		$el.scrollable();

		var api = $el.data("scrollable");

		var month_str;
		// if there is a selected day, scroll to it
		var date = $(".calendar td.highlight.selected").attr('data');
		if (date) {
			month_str = date.substr(0, 7);
		} else {
			// elif the current month is in the list of scrollable items, scroll to it.
			var today = new Date()
			function pad(n){return n<10 ? '0'+n : n}
			month_str = today.getUTCFullYear()+'-'
				+ pad(today.getUTCMonth()+1);
		}

		if (month_str) {
			var offset = 0;
			api.getItems().each(function() {
				var $this = $(this);
				if ($this.attr("data") == month_str) {
					api.move(offset, 0);
					return false;
				}
				offset += 1;
			});
		};
		
		var days_count = 	$("#sessions dt").size();
		
		if (days_count > 1) {
			//Hide sessions
			$("#sessions dt").hide();
			$("#sessions dd").hide();

			//inject an info/results box
			$("#sessions").prepend("<p class='help'>Click on calendar to see session times</p>");
		
			// Make highlighted dates look clickable
			$(".calendar td.highlight").css("cursor", "pointer");

			var highlight_click = function(event) {
				var $this = $(this);
				$(".calendar td.highlight").removeClass("clicked");
				$this.addClass("clicked");
				$("#sessions .help").hide();
				$("#sessions dt").hide();
				$("#sessions dd").hide();
				// show only the sessions with the data
				$("#sessions [data=\""+$this.attr('data')+"\"]").fadeIn(400);

			};
			// Show session data when we click on a date
			$(".calendar td.highlight").click(highlight_click);

			// By default, highlight the initially selected date
			$(".calendar td.highlight.selected").each(highlight_click);

		} // endif
	});

})(jQuery);