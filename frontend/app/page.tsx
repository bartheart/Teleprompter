import Image from "next/image";
import Recorder from "../components/recorder";

export default function Home() {
  return (
    <div>
      <p>LOGO</p>
      <div>
        <form>
          <div>
            <label>Context</label>
            <input type="text"/>
          </div>
          <button type="submit">Start Teleprompter</button>
          
        </form>
      </div>
      <div>
        < Recorder /> 
      </div>
      
    </div>
  );
}
