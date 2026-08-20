import ReactMarkdown from "react-markdown";
import { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,setError] = useState("");
  const [file, setFile] = useState(null);
  const [uploading,setUploading] = useState(false);
  const [uploadMessage,setUploadMessage] = useState("");

  const uploadPDF = async () =>{
    if(!file){
      setUploadMessage("Please select a PDF first.");
      return;
    }

    setUploading(true);
    setUploadMessage("");
    setAnswer("");
    setSources([]);

    try{
      const formData = new FormData();

      formData.append("file",file);

      const response = await fetch(
        "https://pdf-rag-assistant-3dwe.onrender.com/upload",
        {
          method:"POST",
          body: formData,
        }

      );
      if (!response.ok){
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setUploadMessage(data.message);
    }catch (error){
      console.error("Upload error:", error);

      setUploadMessage(
        "Unable to upload the PDF."
      );
    }finally{
      setUploading(false);
    }

  };
  const askQuestion = async () => {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setError("");
    setSources([]);

    try {
      const response = await fetch(
        "https://pdf-rag-assistant-3dwe.onrender.com/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question,
          }),
        }
      );
      if(!response.ok){
        throw new Error("Failed to fetch answer from the server.");
      }

      const data = await response.json();

      setAnswer(data.answer);
      setSources(data.sources ||[]);
      setQuestion("");
    } catch (error) {
      setError("Unable to get an answer. Please try again later.");
      setAnswer("Something went wrong.");
    }finally{
      setLoading(false);

    }
  };

  return (
    <div className="app">
      <div className="container">
        <h1> PDF RAG Assistant</h1>

        <p className ="subtitle">Ask question about your documents</p>

        <div className="upload-box">
          <input
            type="file"
            accept=".pdf"
            onChange={(event) =>
              setFile(event.target.files[0])
            }
          />

          <button onClick={uploadPDF} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload PDF"}
          </button>
        </div>
        {file && (
          <p>
            Selected: {file.name}
          </p>
        )}
        {uploadMessage && (
          <p>
            {uploadMessage}
          </p>
        )}

        

        <div className ="question-box">

          <input
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}

            onKeyDown={(event)=>{
              if(event.key === "Enter"){
                askQuestion();
              }
            }}
            placeholder ="Ask a question..."
          />

          <button 
            onClick={askQuestion}
            disabled={loading}
          >
            {loading ? "Thinking..." : "Ask"}
          </button>

        </div>

        {error && (
          <p className="error">
            {error}
          </p>
        )}

        {answer && (
          <div className ="answer-card">
            <h2>Answer</h2>
            
            <p className ="answer">
              <ReactMarkdown>{answer}</ReactMarkdown>
            </p>
            {sources.length > 0 && (
              <div className="sources">

                <h3>Sources</h3>

                {sources.map((page) => (
                  <span
                    className="source"
                    key={page}
                  >
                    Page {page}
                  </span>
                ))}

              </div>
            )}

          </div>
        )}



      </div>
    </div>
  );
}

export default App;