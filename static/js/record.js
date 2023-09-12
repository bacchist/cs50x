// This is a modified version of Web Dictaphone, a sample webapp provided by
// MDN to demonstrate the MediaRecorder API. I repurposed it by removing the
// visualization elements and the clip storage features. Aside from that, I
// added one small bit of code specific to my application that passes the
// blob containing the recorded audio to the server and uses the response to
// populate the input field of the page.

// set up basic variables for app

const record = document.querySelector('.record');
const stop = document.querySelector('.stop');

// disable stop button while not recording

stop.disabled = true;

//main block for doing the audio recording

if (navigator.mediaDevices.getUserMedia) {
	console.log('getUserMedia supported.');

	const constraints = { audio: true };
	let chunks = [];

	let onSuccess = function(stream) {
		const mediaRecorder = new MediaRecorder(stream);

		record.onclick = function() {
			mediaRecorder.start();
			console.log(mediaRecorder.state);
			console.log("recorder started");

			stop.disabled = false;
			record.disabled = true;
		}

		stop.onclick = function() {
			mediaRecorder.stop();
			console.log(mediaRecorder.state);
			console.log("recorder stopped");
			record.style.background = "";
			record.style.color = "";

			stop.disabled = true;
			record.disabled = false;
		}

		mediaRecorder.ondataavailable = function(e) {
			chunks.push(e.data);
		}

		mediaRecorder.onstop = function(e) {
			console.log("data available after MediaRecorder.stop() called.");


			const blob = new Blob(chunks, { 'type' : 'audio/webm; codecs=opus' });

			chunks = [];
			const audioURL = window.URL.createObjectURL(blob);

			// Send the blob to the server and put the response in the user_prompt field
			fetch('/cs50x', {
				method: 'PUT',
				body: blob
			})
				.then(response => response.json())
				.then(data => {
					document.getElementById('user_prompt').value = data.message;
				})
				.catch((error) => {
					console.error('Error:', error);
				});

		}
	}
	let onError = function(err) {
		console.log('The following error occured: ' + err);
	}

	navigator.mediaDevices.getUserMedia(constraints).then(onSuccess, onError);

} else {
	console.log('getUserMedia not supported on your browser!');
}
