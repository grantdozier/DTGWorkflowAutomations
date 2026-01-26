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
  MenuItem,
} from '@mui/material';
import { ArrowForward, ArrowBack, Add, Delete } from '@mui/icons-material';

interface InternalEquipment {
  id: string;
  name: string;
  equipment_type: string;
  hourly_cost: number;
  condition: string;
}

interface Props {
  data: InternalEquipment[];
  onUpdate: (data: InternalEquipment[]) => void;
  onNext: () => void;
  onBack: () => void;
}

const conditionOptions = ['good', 'fair', 'poor'];

export default function InternalEquipmentStep({ data, onUpdate, onNext, onBack }: Props) {
  const [equipment, setEquipment] = useState<InternalEquipment[]>(
    data.length > 0
      ? data
      : [{ id: '1', name: '', equipment_type: '', hourly_cost: 0, condition: 'good' }]
  );

  const handleAdd = () => {
    setEquipment([
      ...equipment,
      { id: Date.now().toString(), name: '', equipment_type: '', hourly_cost: 0, condition: 'good' },
    ]);
  };

  const handleRemove = (id: string) => {
    if (equipment.length > 1) {
      setEquipment(equipment.filter((e) => e.id !== id));
    }
  };

  const handleChange = (id: string, field: keyof InternalEquipment, value: string | number) => {
    setEquipment(
      equipment.map((e) =>
        e.id === id
          ? { ...e, [field]: field === 'hourly_cost' ? parseFloat(value as string) || 0 : value }
          : e
      )
    );
  };

  const handleNext = () => {
    const validEquipment = equipment.filter((e) => e.name.trim() !== '' && e.hourly_cost > 0);
    onUpdate(validEquipment);
    onNext();
  };

  const handleSkip = () => {
    onUpdate([]);
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Internal Equipment
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Add company-owned equipment and operating costs (optional)
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Hourly Cost ($)</TableCell>
              <TableCell>Condition</TableCell>
              <TableCell width={100}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {equipment.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="e.g., CAT 320 Excavator"
                    value={item.name}
                    onChange={(e) => handleChange(item.id, 'name', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="e.g., Excavator"
                    value={item.equipment_type}
                    onChange={(e) => handleChange(item.id, 'equipment_type', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    type="number"
                    placeholder="0.00"
                    value={item.hourly_cost || ''}
                    onChange={(e) => handleChange(item.id, 'hourly_cost', e.target.value)}
                    size="small"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    select
                    value={item.condition}
                    onChange={(e) => handleChange(item.id, 'condition', e.target.value)}
                    size="small"
                  >
                    {conditionOptions.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </MenuItem>
                    ))}
                  </TextField>
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleRemove(item.id)}
                    disabled={equipment.length === 1}
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
        Add Equipment
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
