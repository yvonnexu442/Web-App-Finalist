$(function(){
	$('#submit').click(function(){
		var eventname = $('#EventName').val();
		var eventtype = $('#EventType').val();
		var datein = $('#startDate').val();
		var dateout = $('#endDate').val();
		var attendance = $('#attendance').val();
		var sqft = $('#sqft').val();
		var totalnights = $('#RoomNights').val();
		var renttotal = $('#RentTotal').val();
		var minfb = $('#FB').val();
		var nhalls = $('#ExhibitHalls').val();
		var nmeeting = $('#MeetingRooms').val();
		var naudi = $('#Auditorium').val();
		var nball = $('#Ballrooms').val();
		var minsqft = $('#Minsqft').val();

		$.ajax({
			url:'/opt',
			data:$('form').serialize(),
			type:'POST',
			function(response){
				obj = JSON.parse(response);
				window.location.href = "/room-page"}
		})
		
		console.log(datein)
		console.log(obj)

		//url: '/submit';
        //window.location.href = "/";
    });

});
