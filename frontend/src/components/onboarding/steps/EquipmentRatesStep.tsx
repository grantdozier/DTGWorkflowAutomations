import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { ArrowForward, ArrowBack, Add, Delete } from '@mui/icons-material';

interface EquipmentRate {
  id: string;
  equipment_type: string;
  hourly_rate: number;
  daily_rate: number;
}

interface Props {
  data: EquipmentRate[];
  onUpdate: (data: EquipmentRate[]) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function EquipmentRatesStep({ data, onUpdate, onNext, onBack }: Props) {
  const [rates, setRates] = useState<EquipmentRate[]>(
    data.length > 0 ? data : [{ id: '1', equipment_type: '', hourly_rate: 0, daily_rate: 0 }]
  );

  const handleAdd = () => {
    setRates([...rates, { id: Date.now().toString(), equipment_type: '', hourly_rate: 0, daily_rate: 0 }]);
  };

  const handleRemove = (id: string) => {
    if (rates.length > 1) {
      setRates(rates.filter((r) => r.id !== id));
    }
  };

  const handleChange = (id: string, field: keyof EquipmentRate, value: string | number) => {
    setRates(
      rates.map((r) =>
        r.id === id
          ? { ...r, [field]: field !== 'equipment_type' ? parseFloat(value as string) || 0 : value }
          : r
      )
    );
  };

  const handleNext = () => {
    const validRates = rates.filter((r) => r.equipment_type.trim() !== '');
    onUpdate(validRates);
    onNext();
  };

  const handleSkip = () => {
    onUpdate([]);
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Equipment Rental Rates
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Add rental equipment rates for budgeting (optional)
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Equipment Type</TableCell>
              <TableCell>Hourly Rate ($)</TableCell>
              <TableCell>Daily Rate ($)</TableCell>
              <TableCell width={100}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rates.map((rate) => (
              <TableRow key={rate.id}>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="e.g., Excavator, Loader, Truck"
                    value={rate.equipment_type}
                    onChange={(e) => handleChange(rate.id, 'equipment_type', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    type="number"
                    placeholder="0.00"
                    value={rate.hourly_rate || ''}
                    onChange={(e) => handleChange(rate.id, 'hourly_rate', e.target.value)}
                    size="small"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    type="number"
                    placeholder="0.00"
                    value={rate.daily_rate || ''}
                    onChange={(e) => handleChange(rate.id, 'daily_rate', e.target.value)}
                    size="small"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleRemove(rate.id)}
                    disabled={rates.length === 1}
                    size="small"
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Button startIcon={<Add />} onClick={handleAdd} sx={{ mt: 2 }}>
        Add Equipment Type
      </Button>

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
