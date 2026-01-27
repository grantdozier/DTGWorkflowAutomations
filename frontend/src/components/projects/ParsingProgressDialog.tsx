import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  CircularProgress,
  Paper,
  Grid,
} from '@mui/material';
import {
  Description,
  AutoAwesome,
  CheckCircle,
  Error as ErrorIcon,
  Image,
  GridOn,
} from '@mui/icons-material';

interface Props {
  open: boolean;
  documentName: string;
  onClose: () => void;
  status: 'idle' | 'converting' | 'tiling' | 'analyzing' | 'extracting' | 'saving' | 'complete' | 'error';
  progress: number;
  currentPage?: number;
  totalPages?: number;
  tilesProcessed?: number;
  totalTiles?: number;
  itemsExtracted?: number;
  error?: string;
}

const steps = [
  { key: 'converting', label: 'Converting PDF to Images', icon: <Image /> },
  { key: 'tiling', label: 'Creating Analysis Tiles', icon: <GridOn /> },
  { key: 'analyzing', label: 'AI Vision Analysis', icon: <AutoAwesome /> },
  { key: 'extracting', label: 'Extracting Materials', icon: <Description /> },
  { key: 'saving', label: 'Saving to Database', icon: <CheckCircle /> },
];

export default function ParsingProgressDialog({
  open,
  documentName,
  onClose,
  status,
  progress,
  currentPage = 0,
  totalPages = 0,
  tilesProcessed = 0,
  totalTiles = 0,
  itemsExtracted = 0,
  error,
}: Props) {
  const getActiveStep = () => {
    switch (status) {
      case 'converting': return 0;
      case 'tiling': return 1;
      case 'analyzing': return 2;
      case 'extracting': return 3;
      case 'saving': return 4;
      case 'complete': return 5;
      default: return 0;
    }
  };

  const getStepStatus = (stepIndex: number) => {
    const activeStep = getActiveStep();
    if (status === 'error') return stepIndex <= activeStep ? 'error' : 'pending';
    if (stepIndex < activeStep) return 'complete';
    if (stepIndex === activeStep) return 'active';
    return 'pending';
  };

  return (
    <Dialog open={open} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesome color="primary" />
          <Typography variant="h6">Parsing Document</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" color="text.secondary">
            Document
          </Typography>
          <Typography variant="body1" fontWeight="medium">
            {documentName}
          </Typography>
        </Paper>

        {status === 'error' ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <ErrorIcon color="error" sx={{ fontSize: 48, mb: 1 }} />
            <Typography variant="h6" color="error" gutterBottom>
              Parsing Failed
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {error || 'An unknown error occurred'}
            </Typography>
          </Box>
        ) : status === 'complete' ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <CheckCircle color="success" sx={{ fontSize: 48, mb: 1 }} />
            <Typography variant="h6" color="success.main" gutterBottom>
              Parsing Complete!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Extracted {itemsExtracted} items from the document
            </Typography>
          </Box>
        ) : (
          <>
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Overall Progress
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {Math.round(progress)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>

            <Stepper activeStep={getActiveStep()} orientation="vertical">
              {steps.map((step, index) => {
                const stepStatus = getStepStatus(index);
                return (
                  <Step key={step.key} completed={stepStatus === 'complete'}>
                    <StepLabel
                      error={stepStatus === 'error'}
                      StepIconComponent={() => (
                        <Box
                          sx={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            bgcolor: stepStatus === 'complete' ? 'success.main' :
                                     stepStatus === 'active' ? 'primary.main' :
                                     stepStatus === 'error' ? 'error.main' : 'grey.300',
                            color: stepStatus === 'pending' ? 'grey.600' : 'white',
                          }}
                        >
                          {stepStatus === 'active' ? (
                            <CircularProgress size={16} color="inherit" />
                          ) : stepStatus === 'complete' ? (
                            <CheckCircle fontSize="small" />
                          ) : stepStatus === 'error' ? (
                            <ErrorIcon fontSize="small" />
                          ) : (
                            step.icon
                          )}
                        </Box>
                      )}
                    >
                      <Typography
                        variant="body2"
                        fontWeight={stepStatus === 'active' ? 'bold' : 'normal'}
                        color={stepStatus === 'pending' ? 'text.secondary' : 'text.primary'}
                      >
                        {step.label}
                      </Typography>
                    </StepLabel>
                    {stepStatus === 'active' && (
                      <StepContent>
                        <Box sx={{ py: 1 }}>
                          {step.key === 'converting' && totalPages > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              Page {currentPage} of {totalPages}
                            </Typography>
                          )}
                          {step.key === 'tiling' && totalTiles > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              Creating tile {tilesProcessed} of {totalTiles}
                            </Typography>
                          )}
                          {step.key === 'analyzing' && (
                            <Typography variant="caption" color="text.secondary">
                              Sending images to Claude Vision API...
                            </Typography>
                          )}
                          {step.key === 'extracting' && (
                            <Typography variant="caption" color="text.secondary">
                              Found {itemsExtracted} items so far...
                            </Typography>
                          )}
                          {step.key === 'saving' && (
                            <Typography variant="caption" color="text.secondary">
                              Saving {itemsExtracted} items to database...
                            </Typography>
                          )}
                        </Box>
                      </StepContent>
                    )}
                  </Step>
                );
              })}
            </Stepper>

            {/* Stats */}
            <Grid container spacing={2} sx={{ mt: 2 }}>
              {totalPages > 0 && (
                <Grid item xs={4}>
                  <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'primary.50' }}>
                    <Typography variant="h6" color="primary">
                      {currentPage}/{totalPages}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Pages
                    </Typography>
                  </Paper>
                </Grid>
              )}
              {totalTiles > 0 && (
                <Grid item xs={4}>
                  <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'secondary.50' }}>
                    <Typography variant="h6" color="secondary">
                      {tilesProcessed}/{totalTiles}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tiles
                    </Typography>
                  </Paper>
                </Grid>
              )}
              {itemsExtracted > 0 && (
                <Grid item xs={4}>
                  <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'success.50' }}>
                    <Typography variant="h6" color="success.main">
                      {itemsExtracted}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Items
                    </Typography>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
