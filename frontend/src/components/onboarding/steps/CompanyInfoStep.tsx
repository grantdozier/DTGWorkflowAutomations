import { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Grid,
} from '@mui/material';
import { ArrowForward } from '@mui/icons-material';

interface Props {
  data: any;
  onUpdate: (data: any) => void;
  onNext: () => void;
}

export default function CompanyInfoStep({ data, onUpdate, onNext }: Props) {
  const [formData, setFormData] = useState({
    name: data.name || '',
    address: data.address || '',
    city: data.city || '',
    state: data.state || '',
    zip: data.zip || '',
    phone: data.phone || '',
    email: data.email || '',
    ...data,
  });

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleNext = () => {
    onUpdate(formData);
    onNext();
  };

  const isValid = formData.name.trim().length > 0;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Company Information
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Tell us about your company
      </Typography>

      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Company Name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            required
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Address"
            value={formData.address}
            onChange={(e) => handleChange('address', e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="City"
            value={formData.city}
            onChange={(e) => handleChange('city', e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            fullWidth
            label="State"
            value={formData.state}
            onChange={(e) => handleChange('state', e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={3}>
          <TextField
            fullWidth
            label="ZIP Code"
            value={formData.zip}
            onChange={(e) => handleChange('zip', e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Phone"
            value={formData.phone}
            onChange={(e) => handleChange('phone', e.target.value)}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
          />
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={!isValid}
          endIcon={<ArrowForward />}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
