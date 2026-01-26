import { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Grid,
  Chip,
} from '@mui/material';
import { Add, Delete, Save, Business, AttachMoney, Percent, Build } from '@mui/icons-material';
import api from '../../services/api';
import Layout from '../../components/Layout';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface LaborRate {
  id: string;
  type: string;
  hourly_rate: number;
}

interface EquipmentRate {
  id: string;
  equipment_type: string;
  hourly_rate: number;
  daily_rate: number;
}

interface OverheadMargins {
  overhead_percentage: number;
  profit_margin_percentage: number;
  bond_percentage: number;
  contingency_percentage: number;
}

interface CompanyInfo {
  id: string;
  name: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Company Info
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({ id: '', name: '' });

  // Labor Rates
  const [laborRates, setLaborRates] = useState<LaborRate[]>([]);

  // Equipment Rates
  const [equipmentRates, setEquipmentRates] = useState<EquipmentRate[]>([]);

  // Overhead & Margins
  const [overheadMargins, setOverheadMargins] = useState<OverheadMargins>({
    overhead_percentage: 10,
    profit_margin_percentage: 10,
    bond_percentage: 0,
    contingency_percentage: 5,
  });

  useEffect(() => {
    fetchAllSettings();
  }, []);

  const fetchAllSettings = async () => {
    try {
      setLoading(true);
      
      // Fetch company info
      const companyRes = await api.get('/company/me');
      setCompanyInfo({ id: companyRes.data.id, name: companyRes.data.name });

      // Fetch company rates
      try {
        const ratesRes = await api.get('/company/rates');
        const rates = ratesRes.data;

        // Parse labor rates from JSON
        if (rates.labor_rate_json) {
          const laborArr = Object.entries(rates.labor_rate_json).map(([type, rate], idx) => ({
            id: `labor-${idx}`,
            type,
            hourly_rate: rate as number,
          }));
          setLaborRates(laborArr.length > 0 ? laborArr : [{ id: 'labor-0', type: '', hourly_rate: 0 }]);
        }

        // Parse equipment rates from JSON
        if (rates.equipment_rate_json) {
          const equipArr = Object.entries(rates.equipment_rate_json).map(([type, rateObj]: [string, any], idx) => ({
            id: `equip-${idx}`,
            equipment_type: type,
            hourly_rate: typeof rateObj === 'object' ? rateObj.hourly || 0 : rateObj,
            daily_rate: typeof rateObj === 'object' ? rateObj.daily || 0 : 0,
          }));
          setEquipmentRates(equipArr.length > 0 ? equipArr : [{ id: 'equip-0', equipment_type: '', hourly_rate: 0, daily_rate: 0 }]);
        }

        // Parse overhead/margins from JSON
        if (rates.overhead_json || rates.margin_json) {
          setOverheadMargins({
            overhead_percentage: rates.overhead_json?.percentage || 10,
            profit_margin_percentage: rates.margin_json?.profit || 10,
            bond_percentage: rates.margin_json?.bond || 0,
            contingency_percentage: rates.margin_json?.contingency || 5,
          });
        }
      } catch (ratesErr: any) {
        // Rates might not exist yet, use defaults
        setLaborRates([{ id: 'labor-0', type: '', hourly_rate: 0 }]);
        setEquipmentRates([{ id: 'equip-0', equipment_type: '', hourly_rate: 0, daily_rate: 0 }]);
      }

      setError('');
    } catch (err: any) {
      console.error('Failed to fetch settings', err);
      setError(err.response?.data?.detail || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAll = async () => {
    try {
      setSaving(true);
      setError('');

      // Update company name
      await api.put('/company/me', { name: companyInfo.name });

      // Build rates payload
      const laborRateJson: Record<string, number> = {};
      laborRates.forEach((r) => {
        if (r.type.trim()) {
          laborRateJson[r.type] = r.hourly_rate;
        }
      });

      const equipmentRateJson: Record<string, { hourly: number; daily: number }> = {};
      equipmentRates.forEach((r) => {
        if (r.equipment_type.trim()) {
          equipmentRateJson[r.equipment_type] = {
            hourly: r.hourly_rate,
            daily: r.daily_rate,
          };
        }
      });

      await api.post('/company/rates/bulk-update', {
        labor_rate_json: laborRateJson,
        equipment_rate_json: equipmentRateJson,
        overhead_json: {
          percentage: overheadMargins.overhead_percentage,
        },
        margin_json: {
          profit: overheadMargins.profit_margin_percentage,
          bond: overheadMargins.bond_percentage,
          contingency: overheadMargins.contingency_percentage,
        },
      });

      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to save settings', err);
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  // Labor rate handlers
  const addLaborRate = () => {
    setLaborRates([...laborRates, { id: `labor-${Date.now()}`, type: '', hourly_rate: 0 }]);
  };

  const removeLaborRate = (id: string) => {
    if (laborRates.length > 1) {
      setLaborRates(laborRates.filter((r) => r.id !== id));
    }
  };

  const updateLaborRate = (id: string, field: keyof LaborRate, value: string | number) => {
    setLaborRates(
      laborRates.map((r) =>
        r.id === id ? { ...r, [field]: field === 'hourly_rate' ? parseFloat(value as string) || 0 : value } : r
      )
    );
  };

  // Equipment rate handlers
  const addEquipmentRate = () => {
    setEquipmentRates([...equipmentRates, { id: `equip-${Date.now()}`, equipment_type: '', hourly_rate: 0, daily_rate: 0 }]);
  };

  const removeEquipmentRate = (id: string) => {
    if (equipmentRates.length > 1) {
      setEquipmentRates(equipmentRates.filter((r) => r.id !== id));
    }
  };

  const updateEquipmentRate = (id: string, field: keyof EquipmentRate, value: string | number) => {
    setEquipmentRates(
      equipmentRates.map((r) =>
        r.id === id
          ? { ...r, [field]: field !== 'equipment_type' ? parseFloat(value as string) || 0 : value }
          : r
      )
    );
  };

  // Overhead handlers
  const updateOverhead = (field: keyof OverheadMargins, value: string) => {
    setOverheadMargins((prev) => ({
      ...prev,
      [field]: parseFloat(value) || 0,
    }));
  };

  const tabConfig = [
    { label: 'Company', icon: <Business fontSize="small" /> },
    { label: 'Labor Rates', icon: <AttachMoney fontSize="small" /> },
    { label: 'Equipment Rates', icon: <Build fontSize="small" /> },
    { label: 'Margins', icon: <Percent fontSize="small" /> },
  ];

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box sx={{ bgcolor: 'white', borderBottom: '1px solid', borderColor: 'grey.200' }}>
        <Container maxWidth="lg">
          <Box sx={{ pt: 4, pb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'grey.900' }}>
                Settings
              </Typography>
              <Button
                variant="contained"
                startIcon={saving ? <CircularProgress size={18} color="inherit" /> : <Save />}
                onClick={handleSaveAll}
                disabled={saving}
                sx={{ 
                  px: 3,
                  py: 1,
                  background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                  },
                }}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
            <Typography variant="body1" color="text.secondary">
              Configure your company rates and default margins
            </Typography>
          </Box>
          
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            sx={{
              '& .MuiTab-root': {
                minHeight: 48,
                px: 3,
              },
              '& .MuiTabs-indicator': {
                height: 3,
                borderRadius: '3px 3px 0 0',
              },
            }}
          >
            {tabConfig.map((tab, index) => (
              <Tab
                key={index}
                icon={tab.icon}
                iconPosition="start"
                label={tab.label}
                sx={{ gap: 1 }}
              />
            ))}
          </Tabs>
        </Container>
      </Box>
      
      <Container maxWidth="lg" sx={{ py: 4 }}>

        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, borderRadius: 2 }} 
            onClose={() => setError('')}
          >
            {error}
          </Alert>
        )}

        {success && (
          <Alert 
            severity="success" 
            sx={{ mb: 3, borderRadius: 2 }} 
            onClose={() => setSuccess('')}
          >
            {success}
          </Alert>
        )}

        <Paper sx={{ borderRadius: 3, overflow: 'hidden' }}>

          {/* Company Info Tab */}
          <TabPanel value={activeTab} index={0}>
            <Box sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Company Information
              </Typography>
              <Box sx={{ maxWidth: 500 }}>
                <TextField
                  fullWidth
                  label="Company Name"
                  value={companyInfo.name}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, name: e.target.value })}
                  sx={{ mb: 3 }}
                  InputProps={{
                    sx: { bgcolor: 'grey.50' },
                  }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Company ID:
                  </Typography>
                  <Chip 
                    label={companyInfo.id} 
                    size="small" 
                    sx={{ fontFamily: 'monospace', fontSize: 12 }}
                  />
                </Box>
              </Box>
            </Box>
          </TabPanel>

          {/* Labor Rates Tab */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Labor Rates
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Define hourly rates for different labor types
                  </Typography>
                </Box>
                <Button 
                  startIcon={<Add />} 
                  onClick={addLaborRate}
                  variant="outlined"
                  sx={{ borderRadius: 2 }}
                >
                  Add Rate
                </Button>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {laborRates.map((rate, index) => (
                  <Box 
                    key={rate.id}
                    sx={{ 
                      display: 'flex', 
                      gap: 2, 
                      alignItems: 'center',
                      p: 2,
                      bgcolor: 'grey.50',
                      borderRadius: 2,
                    }}
                  >
                    <Typography sx={{ width: 30, color: 'grey.400', fontWeight: 500 }}>
                      {index + 1}
                    </Typography>
                    <TextField
                      size="small"
                      placeholder="Labor type (e.g., Foreman)"
                      value={rate.type}
                      onChange={(e) => updateLaborRate(rate.id, 'type', e.target.value)}
                      sx={{ flex: 2, bgcolor: 'white' }}
                    />
                    <TextField
                      size="small"
                      type="number"
                      placeholder="0.00"
                      value={rate.hourly_rate || ''}
                      onChange={(e) => updateLaborRate(rate.id, 'hourly_rate', e.target.value)}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        endAdornment: <InputAdornment position="end">/hr</InputAdornment>,
                      }}
                      sx={{ width: 180, bgcolor: 'white' }}
                    />
                    <IconButton
                      size="small"
                      onClick={() => removeLaborRate(rate.id)}
                      disabled={laborRates.length === 1}
                      sx={{ color: 'grey.400', '&:hover': { color: 'error.main' } }}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Box>
          </TabPanel>

          {/* Equipment Rates Tab */}
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Equipment Rental Rates
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Define rental rates for equipment types
                  </Typography>
                </Box>
                <Button 
                  startIcon={<Add />} 
                  onClick={addEquipmentRate}
                  variant="outlined"
                  sx={{ borderRadius: 2 }}
                >
                  Add Rate
                </Button>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {equipmentRates.map((rate, index) => (
                  <Box 
                    key={rate.id}
                    sx={{ 
                      display: 'flex', 
                      gap: 2, 
                      alignItems: 'center',
                      p: 2,
                      bgcolor: 'grey.50',
                      borderRadius: 2,
                    }}
                  >
                    <Typography sx={{ width: 30, color: 'grey.400', fontWeight: 500 }}>
                      {index + 1}
                    </Typography>
                    <TextField
                      size="small"
                      placeholder="Equipment type (e.g., Excavator)"
                      value={rate.equipment_type}
                      onChange={(e) => updateEquipmentRate(rate.id, 'equipment_type', e.target.value)}
                      sx={{ flex: 2, bgcolor: 'white' }}
                    />
                    <TextField
                      size="small"
                      type="number"
                      placeholder="0.00"
                      value={rate.hourly_rate || ''}
                      onChange={(e) => updateEquipmentRate(rate.id, 'hourly_rate', e.target.value)}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        endAdornment: <InputAdornment position="end">/hr</InputAdornment>,
                      }}
                      sx={{ width: 160, bgcolor: 'white' }}
                    />
                    <TextField
                      size="small"
                      type="number"
                      placeholder="0.00"
                      value={rate.daily_rate || ''}
                      onChange={(e) => updateEquipmentRate(rate.id, 'daily_rate', e.target.value)}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        endAdornment: <InputAdornment position="end">/day</InputAdornment>,
                      }}
                      sx={{ width: 160, bgcolor: 'white' }}
                    />
                    <IconButton
                      size="small"
                      onClick={() => removeEquipmentRate(rate.id)}
                      disabled={equipmentRates.length === 1}
                      sx={{ color: 'grey.400', '&:hover': { color: 'error.main' } }}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            </Box>
          </TabPanel>

          {/* Overhead & Margins Tab */}
          <TabPanel value={activeTab} index={3}>
            <Box sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                Overhead & Profit Margins
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
                These percentages are applied as defaults when creating estimates
              </Typography>

              <Grid container spacing={3} sx={{ maxWidth: 700 }}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Overhead
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      value={overheadMargins.overhead_percentage}
                      onChange={(e) => updateOverhead('overhead_percentage', e.target.value)}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        sx: { bgcolor: 'white', fontSize: 24, fontWeight: 600 },
                      }}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Typical: 8-15%
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Profit Margin
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      value={overheadMargins.profit_margin_percentage}
                      onChange={(e) => updateOverhead('profit_margin_percentage', e.target.value)}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        sx: { bgcolor: 'white', fontSize: 24, fontWeight: 600 },
                      }}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Typical: 8-15%
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Bond
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      value={overheadMargins.bond_percentage}
                      onChange={(e) => updateOverhead('bond_percentage', e.target.value)}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        sx: { bgcolor: 'white', fontSize: 24, fontWeight: 600 },
                      }}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      0 if not bonded
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Contingency
                    </Typography>
                    <TextField
                      fullWidth
                      type="number"
                      value={overheadMargins.contingency_percentage}
                      onChange={(e) => updateOverhead('contingency_percentage', e.target.value)}
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        sx: { bgcolor: 'white', fontSize: 24, fontWeight: 600 },
                      }}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Typical: 3-10%
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </Layout>
  );
}
