function fullSound(){
    let preString = "";
    let soundBool = false;

    let context = new AudioContext();
    let sound = new Audio("music.mp3");
    let source = context.createMediaElementSource(sound);
    let gain = context.createGain();
    let stereoPanner = context.createStereoPanner();
    let distortion = context.createWaveShaper();
    let compressor = context.createDynamicsCompressor();

    source.connect(gain);
    gain.connect(stereoPanner);
    stereoPanner.connect(distortion);
    distortion.connect(compressor);
    compressor.connect(context.destination);

    sound.loop = true;
    gain.gain.value = 1.0;
    stereoPanner.pan.value = 0.0;
    distortionVal = 10
    distortion.curve = makeDistortionCurve(distortionVal);
    distortion.oversample = "4x";
    compressor.threshold.value = -20;

    window.setInterval(function(){
        if (string == "b0 4 1 " && soundBool == false) {
            sound.play();
            soundBool = true;
        }
        else if (string == "b0 4 2 " && soundBool == true) {
            sound.pause();
            soundBool = false;
        }
        else if (string == "b0 4 3 "){
            preString = ""
        }
        
        else if (string == "b0 4 4 "){
            resetGame();
        }
        changeGain();
        changePanning();
        changeDistortion();
        changeThreshold();
    }, 20);

    function changeGain() {
        if (string == "b0 5 1 " && string != preString){
            gain.gain.value -= 0.1;
            preString = string;
        }
        else if (string == "b0 5 2 " && string != preString){
            gain.gain.value += 0.1;
            preString = string;
        }
    }

    function changePanning() {
        if (string == "b0 5 3 " && string != preString){
            stereoPanner.pan.value -= 0.1
            preString = string;
        }
        else if (string == "b0 5 4 " && string != preString){
            stereoPanner.pan.value += 0.1;
            preString = string;
        }
    }

    function changeDistortion() {
        if (string == "b0 5 5 " && string != preString){
            distortionVal -= 1;
            preString = string;
        }
        else if (string == "b0 5 6 " && string != preString){
            distortionVal += 1;
            preString = string;
        }
        distortion.curve = makeDistortionCurve(distortionVal);
    }

    function changeThreshold() {
        if (string == "b0 5 7 " && string != preString){
            compressor.threshold.value -= 2;
            preString = string;
        }
        else if (string == "b0 5 8 " && string != preString){
            compressor.threshold.value += 2;
            preString = string;
        }
    }

    function resetGame() {
        sound.pause();
        sound.currentTime = 0;
        soundBool = false;
        gain.gain.value = 1.0;
        stereoPanner.pan.value = 0.0;
        distortionVal = 10
        distortion.curve = makeDistortionCurve(distortionVal);
        compressor.threshold.value = -20;
    }

    //Distortion Funktion
    function makeDistortionCurve(amount) {    
        let n_samples = 44100,
            curve = new Float32Array(n_samples);
        for (var i = 0; i < n_samples; ++i ) {
            var x = i * 2 / n_samples - 1;
            curve[i] = (Math.PI + amount) * x / (Math.PI + (amount * Math.abs(x)));
        }  
        return curve;
    };
}

var browser = bowser.getParser(window.navigator.userAgent).parsedResult.browser.name;

if (browser == 'Chrome'){
    document.querySelector('#playStopButton').addEventListener('click', function(){
        fullSound();
    });
}
else {
    document.querySelector('#playStopButton').style.opacity = 0;
    fullSound();
}