import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  Container,
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import CompanyInfoStep from './steps/CompanyInfoStep';
import LaborRatesStep from './steps/LaborRatesStep';
import EquipmentRatesStep from './steps/EquipmentRatesStep';
import InternalEquipmentStep from './steps/InternalEquipmentStep';
import OverheadMarginsStep from './steps/OverheadMarginsStep';
import VendorsStep from './steps/VendorsStep';
import ImportHistoryStep from './steps/ImportHistoryStep';
import ReviewStep from './steps/ReviewStep';

const steps = [
  'Company Info',
  'Labor Rates',
  'Equipment Rates',
  'Internal Equipment',
  'Overhead & Margins',
  'Vendors',
  'Import History',
  'Review & Submit',
];

export default function OnboardingWizard() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<any>({
    companyInfo: {},
    laborRates: [],
    equipmentRates: [],
    internalEquipment: [],
    overheadMargins: {},
    vendors: [],
    importHistory: {
      projects: null,
      estimates: null,
    },
  });

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleStepData = (stepKey: string, data: any) => {
    setFormData((prev: any) => ({
      ...prev,
      [stepKey]: data,
    }));
  };

  const handleComplete = async () => {
    // Mark onboarding as complete
    try {
      // This will be called from ReviewStep after saving all data
      await refreshUser();
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to complete onboarding', error);
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <CompanyInfoStep
            data={formData.companyInfo}
            onUpdate={(data) => handleStepData('companyInfo', data)}
            onNext={handleNext}
          />
        );
      case 1:
        return (
          <LaborRatesStep
            data={formData.laborRates}
            onUpdate={(data) => handleStepData('laborRates', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <EquipmentRatesStep
            data={formData.equipmentRates}
            onUpdate={(data) => handleStepData('equipmentRates', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <InternalEquipmentStep
            data={formData.internalEquipment}
            onUpdate={(data) => handleStepData('internalEquipment', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <OverheadMarginsStep
            data={formData.overheadMargins}
            onUpdate={(data) => handleStepData('overheadMargins', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 5:
        return (
          <VendorsStep
            data={formData.vendors}
            onUpdate={(data) => handleStepData('vendors', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 6:
        return (
          <ImportHistoryStep
            data={formData.importHistory}
            onUpdate={(data) => handleStepData('importHistory', data)}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 7:
        return (
          <ReviewStep
            formData={formData}
            onBack={handleBack}
            onComplete={handleComplete}
          />
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" align="center" gutterBottom>
          Welcome to DTG Workflow Automations
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" paragraph>
          Let's set up your company profile
        </Typography>

        <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          <Box>{getStepContent(activeStep)}</Box>
        </Paper>
      </Box>
    </Container>
  );
}
