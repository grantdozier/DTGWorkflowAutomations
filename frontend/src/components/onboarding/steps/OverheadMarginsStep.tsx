import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Grid,
  InputAdornment,
} from '@mui/material';
import { ArrowForward, ArrowBack } from '@mui/icons-material';

interface Props {
  data: any;
  onUpdate: (data: any) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function OverheadMarginsStep({ data, onUpdate, onNext, onBack }: Props) {
  const [formData, setFormData] = useState({
    overhead_percentage: data.overhead_percentage || 10,
    profit_margin_percentage: data.profit_margin_percentage || 10,
    bond_percentage: data.bond_percentage || 0,
    contingency_percentage: data.contingency_percentage || 5,
    ...data,
  });

  const handleChange = (field: string, value: string) => {
    const numValue = parseFloat(value) || 0;
    setFormData((prev) => ({
      ...prev,
      [field]: numValue,
    }));
  };

  const handleNext = () => {
    onUpdate(formData);
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Overhead & Profit Margins
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure your default percentages for estimates
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Overhead Percentage"
            type="number"
            value={formData.overhead_percentage}
            onChange={(e) => handleChange('overhead_percentage', e.target.value)}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{ min: 0, max: 100, step: 0.1 }}
            helperText="Typical range: 8-15%"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Profit Margin Percentage"
            type="number"
            value={formData.profit_margin_percentage}
            onChange={(e) => handleChange('profit_margin_percentage', e.target.value)}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{ min: 0, max: 100, step: 0.1 }}
            helperText="Typical range: 8-15%"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Bond Percentage"
            type="number"
            value={formData.bond_percentage}
            onChange={(e) => handleChange('bond_percentage', e.target.value)}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{ min: 0, max: 100, step: 0.1 }}
            helperText="If applicable (0 if not bonded)"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Contingency Percentage"
            type="number"
            value={formData.contingency_percentage}
            onChange={(e) => handleChange('contingency_percentage', e.target.value)}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{ min: 0, max: 100, step: 0.1 }}
            helperText="Typical range: 3-10%"
          />
        </Grid>
      </Grid>

      <Box
        sx={{
          mt: 3,
          p: 2,
          bgcolor: 'info.lighter',
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'info.main',
        }}
      >
        <Typography variant="body2" color="info.dark">
          <strong>Tip:</strong> These percentages will be used as defaults when creating estimates.
          You can always adjust them for individual projects.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Back
        </Button>
        <Button variant="contained" onClick={handleNext} endIcon={<ArrowForward />}>
          Next
        </Button>
      </Box>
    </Box>
  );
}
