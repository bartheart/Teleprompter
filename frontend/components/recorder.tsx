"use client";
import React, {useEffect, useState, useRef} from "react";
import { Socket, io } from "socket.io-client";

export default function Recorder () {
    const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    const audioRef = useRef<MediaRecorder | null>(null);
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

    // define a function to initialize a socket 
    const initializeSocket = () => {
        // dont create a socket if it exists
        if (socket.current) return;

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

        // get the reponse of the sent audio file 
        newSocket.on('audio_recieved', (response) => {
            console.log("Server Response: ", response);
        });
       
        // save scoket reference 
        socket.current = newSocket
    }



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

            // initialize a socket and connect 
            initializeSocket();
            if (socket.current) {
                // connect the socket 
                socket.current.connect();
                // send the mime type to the backend 
                socket.current.emit('mime_type', mimeType);
            };

            const options = { 
                mimeType: mimeType,
                audioBitsPerSecond: 16000,  
                channelCount: 1 
            };

            // initialize a Mediarecorder instance with the audiostream 
            const recordedMedia = new MediaRecorder(stream, options);
            // update the audio url to the current 
            audioRef.current = recordedMedia;

            // push the recorded media when availabe 
            recordedMedia.ondataavailable = (event) => {
                const audioChunk = event.data;
                if (socket.current?.connected && audioChunk.size > 0){
                    socket.current.emit('audio_data', audioChunk)
                }
            };

            // send the audio file every 100ms 
            recordedMedia.start(100);

            // update the isRecording state 
            setIsRecording(true);

            console.log("Recording started with mime type: ", {mimeType})

        } catch (err) {
            setError("Error starting recording: " + (err as Error).message);
            console.error("Error starting recording:", err);
        }
    }


    //define a function to cleanup resources
    const cleanUp = () => {
        // stop the media recorder instance 
        if (audioRef.current?.state === 'recording') {
            // stop recording 
            audioRef.current.stop();
        };
        audioRef.current = null;

        // stop all audio tracks
        if (audioStream) {
            audioStream.getTracks().forEach((track) => track.stop());
            setAudioStream(null);
            console.log("Audio stream cleanedup.")
        };

        // disconnect the socket 
        if (socket.current?.connected) {
            socket.current.disconnect();
            console.log('Socket disconnected');
        }

        // set is recording to false
        setIsRecording(false);

    };

    // define a function to request the mic permission 
    const handleButton = async () => {
        if (isRecording) {
            // stop recording 
            cleanUp();
        } else {
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
                await startRecording(stream);
    
            } catch (err) {
                const errorMessage = (err as Error).message || "An unknown eror";
                // set the error state
                setError(errorMessage);
                // output the error message 
                console.log("Erorr acessing the mic: ", err)
            };
            
        } 
    };

    
    // clean up the stream when the componenet unmounts 
    useEffect (() => {
        
        return () => {
            cleanUp();
            socket.current = null;
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

        </div>
    );
};