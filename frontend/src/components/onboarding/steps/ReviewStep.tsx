import { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { ArrowBack, CheckCircle } from '@mui/icons-material';
import api from '../../../services/api';

interface Props {
  formData: any;
  onBack: () => void;
  onComplete: () => void;
}

export default function ReviewStep({ formData, onBack, onComplete }: Props) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setSaving(true);
    setError('');

    try {
      // Save company rates (overhead, margins) - use bulk-update to handle create or update
      if (Object.keys(formData.overheadMargins).length > 0) {
        await api.post('/company/rates/bulk-update', {
          overhead_json: {
            percentage: formData.overheadMargins.overhead_percentage || 0,
          },
          margin_json: {
            profit: formData.overheadMargins.profit_margin_percentage || 0,
            bond: formData.overheadMargins.bond_percentage || 0,
            contingency: formData.overheadMargins.contingency_percentage || 0,
          },
          labor_rate_json: formData.laborRates.reduce((acc: any, rate: any) => {
            acc[rate.type] = rate.hourly_rate;
            return acc;
          }, {}),
          equipment_rate_json: formData.equipmentRates.reduce((acc: any, rate: any) => {
            acc[rate.equipment_type] = {
              hourly: rate.hourly_rate,
              daily: rate.daily_rate,
            };
            return acc;
          }, {}),
        });
      }

      // Save internal equipment
      for (const equipment of formData.internalEquipment) {
        if (equipment.name) {
          await api.post('/equipment', {
            name: equipment.name,
            equipment_type: equipment.equipment_type,
            hourly_cost: equipment.hourly_cost,
            condition: equipment.condition,
            is_available: true,
          });
        }
      }

      // Save vendors
      for (const vendor of formData.vendors) {
        if (vendor.name) {
          await api.post('/vendors', {
            name: vendor.name,
            category: vendor.category,
            email: vendor.email || null,
            phone: vendor.phone || null,
          });
        }
      }

      // Import historical data if files provided
      if (formData.importHistory.projects) {
        const formDataProjects = new FormData();
        formDataProjects.append('file', formData.importHistory.projects);
        await api.post('/import/projects', formDataProjects);
      }

      if (formData.importHistory.estimates) {
        const formDataEstimates = new FormData();
        formDataEstimates.append('file', formData.importHistory.estimates);
        await api.post('/import/estimates', formDataEstimates);
      }

      // Mark onboarding as complete
      await api.post('/auth/complete-onboarding');

      // Complete onboarding
      onComplete();
    } catch (err: any) {
      console.error('Failed to save onboarding data', err);
      setError(err.response?.data?.detail || 'Failed to save data. Please try again.');
      setSaving(false);
    }
  };

  const laborRatesCount = formData.laborRates.filter((r: any) => r.type).length;
  const equipmentRatesCount = formData.equipmentRates.filter((r: any) => r.equipment_type).length;
  const internalEquipmentCount = formData.internalEquipment.filter((e: any) => e.name).length;
  const vendorsCount = formData.vendors.filter((v: any) => v.name).length;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Review & Submit
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Review your information and submit to complete onboarding
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          {/* Company Info */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Company Information</strong>
            </Typography>
            <Typography variant="body2">
              {formData.companyInfo.name || 'Not provided'}
            </Typography>
            {formData.companyInfo.address && (
              <Typography variant="body2" color="text.secondary">
                {formData.companyInfo.address}, {formData.companyInfo.city}, {formData.companyInfo.state} {formData.companyInfo.zip}
              </Typography>
            )}
            {formData.companyInfo.phone && (
              <Typography variant="body2" color="text.secondary">
                Phone: {formData.companyInfo.phone}
              </Typography>
            )}
            {formData.companyInfo.email && (
              <Typography variant="body2" color="text.secondary">
                Email: {formData.companyInfo.email}
              </Typography>
            )}
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Rates & Equipment */}
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>
              Labor Rates
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {laborRatesCount} types configured
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>
              Equipment Rental Rates
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {equipmentRatesCount} types configured
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>
              Internal Equipment
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {internalEquipmentCount} items added
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>
              Vendors
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {vendorsCount} vendors added
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Overhead & Margins */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Overhead & Margins</strong>
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Overhead</Typography>
                <Typography variant="body1">{formData.overheadMargins.overhead_percentage || 0}%</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Profit</Typography>
                <Typography variant="body1">{formData.overheadMargins.profit_margin_percentage || 0}%</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Bond</Typography>
                <Typography variant="body1">{formData.overheadMargins.bond_percentage || 0}%</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">Contingency</Typography>
                <Typography variant="body1">{formData.overheadMargins.contingency_percentage || 0}%</Typography>
              </Grid>
            </Grid>
          </Grid>

          {/* Import History */}
          {(formData.importHistory.projects || formData.importHistory.estimates) && (
            <>
              <Grid item xs={12}>
                <Divider />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Historical Data Import</strong>
                </Typography>
                {formData.importHistory.projects && (
                  <Typography variant="body2" color="text.secondary">
                    Projects: {formData.importHistory.projects.name}
                  </Typography>
                )}
                {formData.importHistory.estimates && (
                  <Typography variant="body2" color="text.secondary">
                    Estimates: {formData.importHistory.estimates.name}
                  </Typography>
                )}
              </Grid>
            </>
          )}
        </Grid>
      </Paper>

      <Alert severity="info" sx={{ mb: 3 }}>
        By submitting, you'll complete the onboarding process and gain access to all features.
        You can always update these settings later from the Settings menu.
      </Alert>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />} disabled={saving}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={saving}
          startIcon={saving ? <CircularProgress size={20} /> : <CheckCircle />}
          size="large"
        >
          {saving ? 'Saving...' : 'Complete Onboarding'}
        </Button>
      </Box>
    </Box>
  );
}
