async function setEffect(name) {
    await fetch(`/effect/${name}`);
}