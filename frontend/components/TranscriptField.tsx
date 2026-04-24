import { Card, Chip, Surface, TextArea } from "@heroui/react";

export function TranscriptField() {
    return (
        <Card className="w-auto md:w-2xl">
            <Card.Header>
                <Card.Description className="flex flex-row gap-2">
                    <Chip className="text-muted">00:00</Chip>
                    -
                    <Chip className="text-muted">00:46</Chip>
                </Card.Description>
            </Card.Header>
            <Card.Content>
                <TextArea
                    placeholder="fdklghdkjfgfdnkbnlvcdjkldfnjgbfhsdnjlkgfdjbjbndglkafsnkljfpowejdoasocksmcm,zxzvmawljfiwkojk"
                    className={"border border-border/50 w-full"}
                    variant="secondary"
                />
            </Card.Content>
        </Card>
    )
}