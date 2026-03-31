using UnrealBuildTool;

public class UnrealAIBFL : ModuleRules
{
    public UnrealAIBFL(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "AIModule",
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "UnrealEd",
            "BlueprintGraph",
            "GraphEditor",
            "KismetCompiler",
            "Kismet",
            "BehaviorTreeEditor",
        });
    }
}
