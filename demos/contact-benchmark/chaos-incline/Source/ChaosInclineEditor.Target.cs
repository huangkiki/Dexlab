using UnrealBuildTool;

public class ChaosInclineEditorTarget : TargetRules
{
    public ChaosInclineEditorTarget(TargetInfo target) : base(target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("ChaosIncline");
    }
}
