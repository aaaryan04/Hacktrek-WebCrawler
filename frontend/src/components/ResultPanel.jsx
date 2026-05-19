function ResultPanel({ result, loading }) {

  return (

    <div className="result-panel">

      <h2>Scan Results</h2>

      <div className="terminal-box">

        {

          loading ? (

            <>

              <p>[+] Initializing scan...</p>

              <p>[+] Connecting to target...</p>

              <p>[+] Running reconnaissance...</p>

            </>

          ) : result ? (

            <>

              <p>[+] Scan completed successfully</p>

              {

                result.url && (

                  <p>
                    [+] Target: {result.url}
                  </p>
                )
              }

              {

                result.target && (

                  <p>
                    [+] Target: {result.target}
                  </p>
                )
              }

              {

                result.forms_found && (

                  <p>
                    [+] Forms Found:
                    {" "}
                    {result.forms_found}
                  </p>
                )
              }

              {

                result.subdomains_found && (

                  <p>
                    [+] Subdomains Found:
                    {" "}
                    {result.subdomains_found}
                  </p>
                )
              }

              {

                result.parameters_found && (

                  <p>
                    [+] URL Parameters:
                    {" "}
                    {result.parameters_found}
                  </p>
                )
              }

              {

                result.error && (

                  <p>
                    [-] Error:
                    {" "}
                    {result.error}
                  </p>
                )
              }

            </>

          ) : (

            <>

              <p>[+] Waiting for scan...</p>

              <p>[+] Recon modules ready...</p>

              <p>[+] Enter target URL...</p>

            </>

          )
        }

      </div>

      <pre>
        {
          result
            ? JSON.stringify(result, null, 2)
            : "No results yet..."
        }
      </pre>

    </div>
  );
}

export default ResultPanel;