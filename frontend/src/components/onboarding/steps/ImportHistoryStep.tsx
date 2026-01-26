import { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
} from '@mui/material';
import { ArrowForward, ArrowBack, CloudUpload, Download } from '@mui/icons-material';

interface Props {
  data: any;
  onUpdate: (data: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function ImportHistoryStep({ data, onUpdate, onNext, onBack }: Props) {
  const [projectsFile, setProjectsFile] = useState<File | null>(data.projects || null);
  const [estimatesFile, setEstimatesFile] = useState<File | null>(data.estimates || null);

  const handleProjectsFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setProjectsFile(event.target.files[0]);
    }
  };

  const handleEstimatesFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setEstimatesFile(event.target.files[0]);
    }
  };

  const handleNext = () => {
    onUpdate({
      projects: projectsFile,
      estimates: estimatesFile,
    });
    onNext();
  };

  const handleSkip = () => {
    onUpdate({
      projects: null,
      estimates: null,
    });
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Import Historical Data
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Import past project data to improve estimate accuracy (optional)
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        You can download CSV templates, fill them with your historical data, and upload them here.
        This helps the system learn from your past projects.
      </Alert>

      {/* Historical Projects */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Historical Projects
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Import completed project information (name, job number, costs, margins)
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            href="/api/v1/import/projects/template"
            target="_blank"
          >
            Download Template
          </Button>
          <Button
            variant="contained"
            component="label"
            startIcon={<CloudUpload />}
          >
            Upload CSV
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={handleProjectsFile}
            />
          </Button>
        </Box>

        {projectsFile && (
          <Alert severity="success">
            File selected: {projectsFile.name}
          </Alert>
        )}
      </Paper>

      {/* Historical Estimates */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Historical Estimates
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Import detailed estimate data (bid items, quantities, costs, productivity rates)
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            href="/api/v1/import/estimates/template"
            target="_blank"
          >
            Download Template
          </Button>
          <Button
            variant="contained"
            component="label"
            startIcon={<CloudUpload />}
          >
            Upload CSV
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={handleEstimatesFile}
            />
          </Button>
        </Box>

        {estimatesFile && (
          <Alert severity="success">
            File selected: {estimatesFile.name}
          </Alert>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Back
        </Button>
        <Box>
          <Button onClick={handleSkip} sx={{ mr: 1 }}>
            Skip
          </Button>
          <Button variant="contained" onClick={handleNext} endIcon={<ArrowForward />}>
            Next
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
