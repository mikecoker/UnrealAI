#pragma once

#include "Modules/ModuleManager.h"

class FUnrealAIBFLModule : public IModuleInterface
{
public:
    virtual void StartupModule() override {}
    virtual void ShutdownModule() override {}
};
