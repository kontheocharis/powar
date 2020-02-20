
@dataclass
class Module(BaseConfig):
    install: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    system_packages: List[str] = field(default_factory=list)
    depends: List[str] = field(default_factory=list)
    exec_before: str = None
    exec_after: str = None
