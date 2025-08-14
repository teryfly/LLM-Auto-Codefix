import React from 'react';
import './PipelineGraph.css';
interface Job {
  id: number;
  name: string;
  status: string;
  stage?: string;
}
interface PipelineStatus {
  pipeline_id?: number;
  status?: string;
  ref?: string;
}
interface PipelineGraphProps {
  jobs: Job[];
  pipelineStatus: PipelineStatus;
}
export const PipelineGraph: React.FC<PipelineGraphProps> = ({ jobs, pipelineStatus }) => {
  // Group jobs by stage
  const jobsByStage = jobs.reduce((acc, job) => {
    const stage = job.stage || 'unknown';
    if (!acc[stage]) {
      acc[stage] = [];
    }
    acc[stage].push(job);
    return acc;
  }, {} as Record<string, Job[]>);
  const stages = Object.keys(jobsByStage);
  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#28a745';
      case 'failed': return '#dc3545';
      case 'running': return '#007bff';
      case 'pending': return '#ffc107';
      case 'canceled': return '#6c757d';
      default: return '#e9ecef';
    }
  };
  return (
    <div className="pipeline-graph">
      <div className="graph-header">
        <h4>Pipeline Visualization</h4>
        <div className="pipeline-info">
          Pipeline #{pipelineStatus.pipeline_id} - {pipelineStatus.status}
        </div>
      </div>
      <div className="stages-container">
        {stages.map((stage, stageIndex) => (
          <div key={stage} className="stage-column">
            <div className="stage-header">
              <h5>{stage}</h5>
            </div>
            <div className="stage-jobs">
              {jobsByStage[stage].map((job, jobIndex) => (
                <div
                  key={job.id}
                  className="job-node"
                  style={{ backgroundColor: getJobStatusColor(job.status) }}
                  title={`${job.name} - ${job.status}`}
                >
                  <span className="job-name">{job.name}</span>
                  <span className="job-status">{job.status}</span>
                </div>
              ))}
            </div>
            {stageIndex < stages.length - 1 && (
              <div className="stage-connector">→</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};