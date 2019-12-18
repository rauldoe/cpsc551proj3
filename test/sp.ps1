# Loop through the server list
Get-Content "ServerList.txt" | %{

  # Define what each job does
  $ScriptBlock = {
    param($pipelinePassIn) 
    Test-Path "\\$pipelinePassIn\c`$\Something"
    Start-Sleep 60
  }

  # Execute the jobs in parallel
  Start-Job $ScriptBlock -ArgumentList $_
}

Get-Job

# Wait for it all to complete
While (Get-Job -State "Running")
{
  Start-Sleep 10
}

# Getting the information back from the jobs
Get-Job | Receive-Job