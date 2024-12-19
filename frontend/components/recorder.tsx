"use client";
import React, {useEffect, useState, useRef} from "react";
import { Socket, io } from "socket.io-client";

export default function Recorder () {
    const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    // define a state to save the audio chunks and the url 
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const audioRef = useRef<MediaRecorder | null>(null);
    const audioChunks = useRef<Blob[]>([]);
    // define a state to handle the is recording button states
    const [isRecording, setIsRecording] = useState<boolean>(false);
    // define a reference for the socket 
    const socket = useRef<Socket | null >(null);
    // define a state for socket is connected
    const [isConnected, setIsConnected] = useState<boolean>(false);

    // define a function to find the compatible mime type by the browser
    const getCompatibleMime = () => {
        const types = [
            'audio/webm',
            'audio/webm;codecs=opus',
            'audio/mp4',
            'audio/mp4;codecs=opus',
            'audio/ogg',
            'audio/ogg;codecs=opus'
        ];

        // iterate over the mime types 
        for (const type of types) {
            // check if the type is compatible 
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return null;
    };



    // define a function that handles recording the audio 
    const startRecording = (stream: MediaStream) => {
        // check if usermedia is not available 
        if (!stream) return;

        try {
            const mimeType = getCompatibleMime();

            // check if there is any comaptibe mime for the browser 
            if (!mimeType){
                throw new Error("No supported audio MIME type found");
            }

            const options = { mimeType };

            // initialize a Mediarecorder instance with the audiostream 
            const recordedMedia = new MediaRecorder(stream, options);
            // update the audio url to the current 
            audioRef.current = recordedMedia;

            // reset previous chunks 
            audioChunks.current = []

            // push the recorded media when availabe 
            recordedMedia.ondataavailable = (event) => {
                audioChunks.current.push(event.data);
            };

            // start recording the audio for 250 seconds 
            recordedMedia.start(250);

            // update the isRecording state 
            setIsRecording(true);

            console.log("Recording started with mime type: ", {mimeType})



        } catch (err) {
            setError("Error starting recording: " + (err as Error).message);
            console.error("Error starting recording:", err);
        }
    }


    //define a function to stop recording 
    const stopRecording = () => {
        // load the recorded media so far 
        const recordedMedia = audioRef.current;

        // check if the recordedMedia and the status is active 
        if (recordedMedia && recordedMedia.state !== 'inactive'){
            // stop the recording 
            recordedMedia.stop();

            // update the isRecording state to false
            setIsRecording(false);

            console.log("Recoding stopped");

            // create a blob and generate a url 
            recordedMedia.onstop = () => {

                try {
                    // try to use the started mime type
                    const mimeType = recordedMedia.mimeType || getCompatibleMime()

                    // create a blob instance with the recorded media 
                    const audioBlob  =  new Blob(audioChunks.current, {type: mimeType || "audio/webm"});

                    // generate the audio url 
                    const audioUrl = URL.createObjectURL(audioBlob);
                    // set the state of the url 
                    setAudioUrl(audioUrl);

                    console.log("Audio recorded and saved!");
                } catch (err) {
                    setError("Error saving audio: " + (err as Error).message);
                    console.error("Error saving audio:", err);
                }
                
            };
        };

    };

    // define a function to request the mic permission 
    const handleButton = async () => {
        if (isRecording) {
            // stop recording 
            stopRecording();
        } else {
            // Request mic access and start recording
            if (!audioStream) {
                try {
                    // capture the audio stream from the mediadvice api
                    const stream: MediaStream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });
                    // set the audiostream state 
                    setAudioStream(stream);
                    // start recording 
                    startRecording(stream);
                    // feedback regarding the mic acess
                    console.log("Mic acess granted!")
        
                } catch (err) {
                    const errorMessage = (err as Error).message || "An unknown eror";
                    // set the error state
                    setError(errorMessage);
                    // output the error message 
                    console.log("Erorr acessing the mic: ", err)
                };
            } else {
                startRecording(audioStream);
            }
        } 
    };

    
    // clean up the stream when the componenet unmounts 
    useEffect (() => {
        // creating a socket instance 
        const newSocket = io("http://127.0.0.1:8000", {
            transports: ['websocket'],
            autoConnect: true,
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });

        // Add error handling
        newSocket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
        });


        // connect with the server 
        newSocket.on('connect', () => {
            console.log("Connected to websocket server");
            setIsConnected(true);
        })

        newSocket.on('disconnect', () => {
            console.log("Disconnected from websocket server");
            setIsConnected(false);
        });

        // save scoket reference 
        socket.current = newSocket

        return () => {
            if (newSocket) {
                newSocket.disconnect();
            };

            if (audioStream) {
                audioStream.getTracks().forEach((track) => track.stop());
            };
        };
    }, []);

    return (
        <div>
            <div>
                <p>Socket status: {isConnected ? 'Connected' : 'Disconnected'}</p>
            </div>
            <button onClick={handleButton}>
                {isRecording ? "Stop": "Start"}
            </button>

            

            { audioUrl && (
                <div>
                    <p>Recorded audio:</p>
                    <audio controls src={audioUrl}></audio>
                </div>
            ) }

        </div>
    );
};